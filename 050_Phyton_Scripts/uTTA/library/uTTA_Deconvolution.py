import numpy as np
from scipy.signal import find_peaks
from skimage import restoration    # scikit-image
import library.uTTA_data_processing as udProc
import library.uTTA_data_plotting as ud_plot
import logging

import numpy as np
import scipy.fft as fft
from scipy.interpolate import interp1d
from scipy import signal # Importiere SciPy für die Residuenbestimmung
from scipy.optimize import nnls

class UttaDeconvolution:

    def __init__(self, logger=None):

        if logger is None:
            self.logger = logging.getLogger("dummy")
            self.logger.addHandler(logging.NullHandler())
            self.logger.propagate = False # Important: prevents forwarding to the root logger
        else:
            self.logger = logger

        # Variables for the Zth deconvolution with Lucy-Richardson Algorithm
        self.rth_stat = 0
        self.deconv_samples_per_decade = 80
        self.z_raw = np.array([])       # the raw converted cooling time base, basically just ln(t)
        self.zth_raw = np.array([])  # the raw converted cooling time base, basically just ln(t)
        self.z = np.array([])           # interpolated, equidistant linear ln(t)-timebase

        self.a_z = np.array([])         # interpolated input Zth-curve with timebase z
        self.dadz = np.array([])        # differentiated input Zth-curve
        self.w_z = np.array([])         # weighing function  --> exp(z - exp(z)), needed for interpolation
        #self.deconv_z_shift = 0         # deconv_z_shift = -2.82660000000
        self.deconvolved = np.array([])
        self.dadz_deconvolved = np.array([])
        self.zth_deconvolved = np.array([])
        self.peaks = np.array([])
        self.iterations = 1000

        # Additional experimental curves
        self.ref_z = np.array([])       # reference curve with a known reference RC Element of 1Ohm and 1F = 1tau
        self.ref_dadz = np.array([])    # differentiated reference curve
        self.ref_peaks = np.array([])
        self.ref_deconv = np.array([])

    def import_zth_input_data(self, timebase, zth):
        """
        Import zth-data and their timebase into the class from two independent arrays of the same length

        Args:
            timebase (list oder numpy.array): timepoints when the zth samples were taken
            zth      (list oder numpy.array): thermal impedances at a given time

        Returns:
            None
                
        Raises:
            ValueError: When array length are not the same
        """

        if len(timebase) != len(zth):
            raise ValueError("Array length must be the same")
        self.z_raw = np.log(timebase)
        self.zth_raw = zth
    
    def import_from_postprocess(self, utta_postprocess:udProc.UttaZthProcessing):
        """
        Imports zth-data and the timebase into the classs for processing

        Args:
            utta_postprocess (UttaZthProcessing): uTTA Postprocessing class

        Returns:
            None
                
        Raises:
            ValueError: When postprocessing class has no data to hand over
        """

        if not utta_postprocess.flag_import_successful:
            raise ValueError("No data to load from UttaZthProcessing")
        self.z_raw = np.log(utta_postprocess.time_cooling)
        self.zth_raw = utta_postprocess.zth[0, :]

    def prepare_zth_deconvolution(self):
        """
        Prepares imported data for the upcoming deconvolution:
            - prepares a new, evenly spaced timebase in ln(t)-space
            - do the differentiation (da/dz) of the input curve
            - create the reference function (greens function) for the deconvolution

        Args:
            None

        Returns:
            None
                
        Raises:
            None
        """
        no_sample_points = int((self.z_raw[-1] - self.z_raw[0]) * self.deconv_samples_per_decade)
        self.logger.info(f"Number of SamplePoints: {no_sample_points}")

        log_samp_point_intervall = (self.z_raw[-1] - self.z_raw[0]) / no_sample_points
        self.logger.info(f"SamplePoint Intervall: {log_samp_point_intervall}")

        z = np.linspace(start=self.z_raw[0], stop=self.z_raw[-1], num=no_sample_points) # create constant step width timebase
        self.a_z = np.interp(z, self.z_raw, self.zth_raw)

        self.rth_stat = np.mean(self.a_z[int(0.98 * len(self.a_z)):-1])
        self.logger.info(f"Zth end value: {self.rth_stat:.3f}, Zth Curve Start Value {self.zth_raw[0]}K/W")

        self.dadz = np.diff(self.a_z) / np.diff(z)
        self.w_z = np.exp(z - np.exp(z))
        self.z = z

        return

    def deconvolve_get_peaks(self, dadz, w_z, iterations):
        """
        Deconvolve the prepared signal by using the Lucy-Richardson deconvolution algorithm.
        After deconvolution, try to find the visible peaks as a first attempt to identify the equivalent RC-elements
        """
        deconv = restoration.richardson_lucy(dadz, self.w_z[:-1] / np.sum(w_z[:-1]),
                                             num_iter=iterations,
                                             clip=False)  # * sum_ref_dadz
        peaks, _ = find_peaks(deconv)

        rth, cth = self.subsample_spectrum(np.exp(self.z[:-1]), deconv, height_threshold=0.000005, distance=1)
        self.logger.info(f"Subsampled Foster:{len(rth)}R/{len(cth)}C\nRth:{rth}\nCth:{cth}")

        rth_cauer, cth_cauer = self.foster_to_cauer_robust(rth, cth)

        self.logger.info(f"Cauer Network: {len(rth_cauer)}R/{len(cth_cauer)}C\nRth:{rth_cauer}\nCth:{cth_cauer}")

        return deconv, peaks
    
    def deconvolve_zth_lucy_richardson(self, iterations):
        self.iterations = iterations
        self.deconvolved, self.peaks = self.deconvolve_get_peaks(self.dadz, self.w_z, iterations)

        self.dadz_deconvolved = (np.convolve(self.deconvolved, self.w_z, "same")) * (self.z[2] - self.z[1])
        self.zth_deconvolved = (np.cumsum(self.dadz_deconvolved) / np.sum(self.deconvolved)) * self.rth_stat + self.a_z[0]

        # print(self.fit_nnls())
        return
    
    def fit_nnls(self, n_tau=60):
        """
        Non-Negative Least Squares spectral fitting.
        
        Pros: Physically 'exact'; guaranteed non-negative; very sharp.
        Cons: Discrete/Spiky output; harder to identify bulk layers.
        """
        tau_grid = np.linspace(self.z[0], self.z[-1], n_tau)
        A = 1 - np.exp(-np.exp(self.z) / tau_grid)
        r_weights, _ = nnls(A, self.zth_raw)
        
        self.spectrum = np.zeros_like(self.z)
        dz = np.mean(np.diff(self.z))
        for r, tau in zip(r_weights, tau_grid):
            idx = np.argmin(np.abs(np.exp(self.z) - tau))
            self.spectrum[idx] = r / dz
        return r_weights, tau_grid

    def subsample_spectrum(self, tau, r_spectrum, height_threshold=0.01, distance=5):
        """
        Identifies major thermal stages and reduces the spectrum to 
        a manageable number of Foster RC pairs.
        """
        # 1. Find peaks in the spectrum
        # height_threshold: Ignore tiny noise peaks (e.g., < 1% of max)
        # distance: Minimum separation between peaks to avoid over-fitting
        peaks, properties = find_peaks(r_spectrum, 
                                    height=np.max(r_spectrum) * height_threshold,
                                    distance=distance)
        
        sub_r = []
        sub_tau = []
        
        # 2. Integrate the resistance around each peak
        # We define the boundaries of a 'peak' as the midpoints between peaks
        boundaries = []
        if len(peaks) > 1:
            midpoints = (peaks[:-1] + peaks[1:]) // 2
            boundaries = [0] + list(midpoints) + [len(r_spectrum)]
        else:
            boundaries = [0, len(r_spectrum)]

        for i in range(len(peaks)):
            start, end = boundaries[i], boundaries[i+1]
            
            # Total resistance for this thermal layer
            peak_r = np.sum(r_spectrum[start:end])
            
            # Weighted average of the time constant (center of gravity of the peak)
            # This is more accurate than just taking the peak's apex
            peak_tau = np.sum(r_spectrum[start:end] * tau[start:end]) / peak_r
            
            sub_r.append(peak_r)
            sub_tau.append(peak_tau)
            
        # Convert to Foster Capacitances
        sub_r = np.array(sub_r)
        sub_tau = np.array(sub_tau)
        sub_c = sub_tau / sub_r
        
        return sub_r, sub_c

    def foster_to_cauer_robust(self, r_foster, c_foster, tol=1e-15):
        """
        Robust conversion with numerical stability guards.
        """
        # 1. Clean data: Remove any non-physical or zero stages
        mask = (r_foster > 0) & (c_foster > 0)
        r_f, c_f = r_foster[mask], c_foster[mask]
        
        # Sort by time constant (Required for stability in continued fractions)
        idx = np.argsort(r_f * c_f)
        r_f, c_f = r_f[idx], c_f[idx]

        # 2. Construct Z(s)
        num = np.poly1d([0.0])
        den = np.poly1d([1.0])
        
        for r, c in zip(r_f, c_f):
            term_num = np.poly1d([r])
            term_den = np.poly1d([r*c, 1.0])
            num = num * term_den + term_num * den
            den = den * term_den

        cauer_r = []
        cauer_c = []
        
        p, q = num, den
        
        # 3. Expansion with stability guards
        for i in range(len(r_f)):
            # Division for C (Shunt element)
            quot_c, rem_c = np.polydiv(q, p)
            
            # Guard against zero/NaN quotients
            if len(quot_c.coeffs) == 0 or np.abs(quot_c.coeffs[0]) < tol:
                break
            cauer_c.append(quot_c.coeffs[0])
            
            # Step: Divide P by Remainder to find R (Series element)
            # First, strip tiny leading coefficients from the remainder (the 'noise')
            rem_c_coeffs = rem_c.coeffs[np.abs(rem_c.coeffs) > tol]
            if len(rem_c_coeffs) == 0:
                break
            rem_c_clean = np.poly1d(rem_c_coeffs)

            quot_r, rem_r = np.polydiv(p, rem_c_clean)
            
            if len(quot_r.coeffs) == 0 or np.abs(quot_r.coeffs[0]) < tol:
                break
            cauer_r.append(quot_r.coeffs[0])
            
            # Clean the next P for the next iteration
            rem_r_coeffs = rem_r.coeffs[np.abs(rem_r.coeffs) > tol]
            if len(rem_r_coeffs) == 0:
                break
            p, q = np.poly1d(rem_r_coeffs), rem_c_clean
            
        return np.array(cauer_r), np.array(cauer_c)

    def foster_to_cauer(self, r_foster, c_foster):
        """
        Converts a Foster network to a Cauer ladder.
        Uses np.polydiv for polynomial long division.
        """
        # 1. Build the Impedance function Z(s) = Num(s) / Den(s)
        # Z(s) = sum( Ri / (1 + s*Ri*Ci) )
        num = np.poly1d([0.0])
        den = np.poly1d([1.0])
        
        for r, c in zip(r_foster, c_foster):
            # Term: R / (1 + sRC)
            term_num = np.poly1d([r])
            term_den = np.poly1d([r*c, 1.0])
            
            # Add fractions: (num1*den2 + num2*den1) / (den1*den2)
            num = num * term_den + term_num * den
            den = den * term_den
        
        # 2. Continuous Fraction Expansion (Successive Polynomial Division)
        cauer_r = []
        cauer_c = []
        
        p, q = num, den
        
        # Each stage of the ladder consists of one Shunt C and one Series R
        for _ in range(len(r_foster)):
            # Step A: Divide Q(s) by P(s) to find the Shunt Capacitance (Cs)
            # quot_c is the quotient, rem_c is the remainder
            quot_c, rem_c = np.polydiv(q, p)
            
            # The quotient is a polynomial of degree 1 (e.g., [C, 0])
            # We take the leading coefficient as the capacitance value
            cauer_c.append(quot_c.coeffs[0])
            
            # Step B: Divide P(s) by the Remainder to find the Series Resistance (Rs)
            quot_r, rem_r = np.polydiv(p, rem_c)
            
            # The quotient is a constant (degree 0) representing Resistance
            cauer_r.append(quot_r.coeffs[0])
            
            # Update for next iteration: P becomes the remainder of R, Q becomes remainder of C
            p, q = rem_r, rem_c
            
        return np.array(cauer_r), np.array(cauer_c)
        
    def foster2cauer_transform(self, RthFoster, CthFoster):
        """ Transformiert die Parameter eines Foster-RC-Netzwerks (Typ I) in die Parameter eines Cauer-RC-Leiternetzwerks (Typ II).
            Die Transformation erfolgt über die Kettenbruch-Expansion (Cauer-Synthese) der Admittanzfunktion Y(s).

            Foster Type I Impedanzfunktion:
            Z(s) = sum(R_i / (1 + s * R_i * C_i))

            Cauer Type II Admittanzfunktion (Serienwiderstände, Parallelkapazitäten):
            Y(s) = 1/r_1 + 1/(r_2 + 1/(s*c_2 + 1/(r_3 + ...)))
            
            Args:
                RthFoster (list oder numpy.array): Widerstände [R1, R2, ...] des Foster-Netzwerks.
                CthFoster (list oder numpy.array): Kapazitäten [C1, C2, ...] des Foster-Netzwerks.
            Returns:
                tuple: (RthCauer, CthCauer), Widerstände und Kapazitäten des Cauer-Netzwerks.
                    RthCauer = [r1, r2, r3, ...] (Serienwiderstände)
                    CthCauer = [c1, c2, c3, ...] (Parallelkapazitäten)
            Raises:
                ValueError: Wenn die Anzahl der R- und C-Elemente nicht übereinstimmt.
        """
        RthFoster = np.array(RthFoster, dtype=float)
        CthFoster = np.array(CthFoster, dtype=float)

        print(f"Rth Foster {RthFoster}\nCth Foster {CthFoster}")

        if len(RthFoster) != len(CthFoster):
            raise ValueError("The number of Foster elements must be equal.")

        N = len(RthFoster)
        if N == 0:
            return [], []

        # 1. Bestimme die Pole und Residuen der Admittanz Y(s)
        # Für das Foster-RC-Netzwerk (Typ I) gilt:
        # Z(s) = sum_{i=1}^{N} (R_i / (1 + s * R_i * C_i))
        # Y(s) = 1/Z(s)
        
        # Vereinfachung: Die Admittanz eines RC-Netzwerks ist analytisch schwer darzustellen.
        # Wir verwenden den Kettenbruch-Algorithmus, der direkt auf der Impedanzfunktion Z(s) oder deren Koeffizienten basiert.
        
        # ----------------------------------------------------------------------
        # Kettenbruch-Expansion der Impedanz Z(s) / s (oder Y(s) / s)
        # ----------------------------------------------------------------------
        # Z(s) lässt sich als Z(s) = P(s) / Q(s) darstellen, wobei
        # P(s) = a_n * s^n + ... + a_1 * s + a_0
        # Q(s) = b_n * s^n + ... + b_1 * s + b_0 
        
        # Zunächst müssen die Koeffizienten des Zählers (P) und des Nenners (Q) der rationalen Funktion Z(s) bestimmt werden. 
        # Grad N, da N parallele RC-Glieder.
        
        # Bestimme die Koeffizienten P(s) und Q(s)
        # Z(s) = P(s) / Q(s)
        
        # Die Pole von Z(s) sind p_i = -1 / (R_i * C_i).
        poles = -1.0 / (RthFoster * CthFoster)
        
        # Koeffizienten Q(s) (Nennerpolynom): Q(s) = Produkt_{i=1}^{N} (s - p_i)
        Q_coeffs = np.poly(poles)
        
        # Koeffizienten P(s) (Zählerpolynom): P(s) hat Grad N-1.
        P_coeffs = np.zeros(N)
        
        # Zähler-Koeffizienten P(s) berechnen, P(s) = Z(s) * Q(s)
        # P(s) = sum_{i=1}^{N} [ R_i * Produkt_{j=1, j!=i}^{N} (s - p_j) ]
        
        for i in range(N):
            # Basis-Polynom (Q(s) ohne den Pol i)
            Q_prime_coeffs = np.poly(np.delete(poles, i))
            
            # Multipliziere mit dem Residuum R_i
            term_coeffs = RthFoster[i] * Q_prime_coeffs
            
            # Addiere zum Gesamt-Zählerpolynom (muss auf Grad N-1 normiert werden)
            # Die Koeffizienten-Arrays haben unterschiedliche Längen.
            P_coeffs = np.add(P_coeffs, np.pad(term_coeffs, (N - len(term_coeffs), 0), 'constant'))
            
        # Die Cauer-Synthese beginnt mit der Kettenbruchentwicklung von Z(s) oder 1/Y(s) = Z(s).
        
        # Es wird die Kettenbruchentwicklung von Z(s) durchgeführt:
        # Z(s) = Z1(s) = r1 + 1 / (s*c1 + 1 / (r2 + 1 / (...)))
        # Da wir ein RC-Netzwerk haben, wechseln sich die Terme (r_i, 1/(s*c_i)) ab.
        
        RthCauer = []
        CthCauer = []
        
        # P_k ist das Zählerpolynom, Q_k ist das Nennerpolynom der verbleibenden Impedanz Z_k(s)
        P_k = P_coeffs
        Q_k = Q_coeffs
        
        for k in range(N):
            # 1. Schritt: Bestimme r_{k+1} aus Z_k(s)
            # r_{k+1} = lim_{s->inf} Z_k(s)
            # r_{k+1} = P_k_highest_coeff / Q_k_highest_coeff
            
            # Höchster Koeffizient von P_k (Grad N-k)
            P_high = P_k[0]
            # Höchster Koeffizient von Q_k (Grad N-k+1) - *Achtung: Grad von Q ist immer einen höher als P, ausser beim letzten Schritt.*
            Q_high = Q_k[0] 

            # Bestimme den Koeffizienten der Serienwiderstände (r_i).
            # Der erste Koeffizient ist der von s^N in Q_k und s^{N-1} in P_k.
            # Da Z(s) ein RC-Impedanz ist, ist der Grad des Zählers immer um 1 kleiner als der Grad des Nenners:
            
            # Bei geradem Index k (0, 2, ...), bestimmen wir den Widerstand r_i
            if k % 2 == 0: # Bestimme r_i = r_{k/2 + 1}
                # r_i = P[0] / Q[0] -> Die Impedanz muss den Grad (N-i) / (N-i) haben.
                # Hier: Z(s) = P/Q, wobei deg(Q) = deg(P)+1.
                # Wir expandieren Y(s) = 1/Z(s) = Q/P mit Y(s) = c1*s + 1/Z1(s)
                
                # Wende den Cauer-Algorithmus auf Y(s) = Q(s) / P(s) an (Typ II)
                # Y_k(s) = c_i * s + 1 / Y_{k+1}(s)

                P_k_new = []
                Q_k_new = []
                
                if k == 0:
                    # Wir expandieren 1/Z(s) = Y(s) = Q(s) / P(s)
                    P_k_new = Q_coeffs # Zähler Q(s)
                    Q_k_new = P_coeffs # Nenner P(s)
                
                # Bei geradem k (d.h. erster Schritt, dritter Schritt...), extrahiere die Kapazität c_i.
                
                # Koeffizient des höchsten s-Terms (Grad N-k)
                P_high = P_k_new[0] 
                # Koeffizient des nächstniedrigeren s-Terms (Grad N-k-1)
                Q_high = Q_k_new[0]
                
                # c_i = P_high / Q_high
                c_i = P_high / Q_high
                CthCauer.append(c_i)
                
                # Subtraktionsschritt: P_new = P - c_i * s * Q
                # Multiplikation von Q_k_new mit c_i * s
                Q_mult = np.pad(Q_k_new * c_i, (0, 1), 'constant')
                
                # Subtraktion: P_k_new - Q_mult (Array-Länge anpassen)
                P_new = P_k_new - Q_mult
                
                # Nächste Admittanz: Y_{k+1}(s) = Q_k_new / P_new
                Q_k = P_new # Neuer Nenner
                P_k = Q_k_new # Neuer Zähler
                
                
            else: # Bestimme r_i = r_{(k+1)/2}
                # Wende den Cauer-Algorithmus auf Z(s) = 1/Y(s) = P/Q an
                # Z_k(s) = r_i + 1 / Z_{k+1}(s)
                
                # Koeffizient des höchsten s-Terms (Grad N-i)
                P_high = P_k[0]
                # Koeffizient des nächstniedrigeren s-Terms (Grad N-i-1)
                Q_high = Q_k[0]
                
                # r_i = P_high / Q_high
                r_i = P_high / Q_high
                RthCauer.append(r_i)
                
                # Subtraktionsschritt: P_new = P - r_i * Q
                P_new = P_k - r_i * Q_k
                
                # Nächste Impedanz: Z_{k+1}(s) = Q_k / P_new
                Q_k = P_new # Neuer Nenner
                P_k = Q_k # Neuer Zähler
                
            
            # Eliminiere führende Nullen
            P_k = P_k[np.nonzero(P_k)] # type: ignore
            Q_k = Q_k[np.nonzero(Q_k)]
            
            if len(P_k) == 0 or len(Q_k) == 0:
                break

        # RthCauer und CthCauer sind nun berechnet.
        # Wichtig: Die Cauer-Synthese wechselt zwischen c_i * s und r_i.
        # Der Zählergrad und Nennergrad ändern sich ständig.
        
        # Richtig wäre: Z(s) -> Y1(s) -> Z2(s) -> Y3(s) -> Z4(s) ...
        # Y(s) = c1*s + 1/Z1(s) (c1 ist die Parallelkapazität)
        # Z1(s) = r1 + 1/Y2(s) (r1 ist der Serienwiderstand)
        
        # Aufgrund der Komplexität der Koeffizientenbestimmung in Python (insbesondere bei rationalen Funktionen) wird hier das 
        # **Cauer Type I (Serien-R, Parallel-C) auf Admittanz** verwendet, das am häufigsten für thermische Modelle verwendet wird.
        
        # Der Ansatz oben ist extrem fehleranfällig wegen der Polynom-Koeffizienten-Darstellung und wird durch eine direkt auf den Residuen basierende Methode ersetzt, 
        # die einfacher ist und oft für die thermische Analyse verwendet wird (Transformation über die Strukturfunktion).

        # ----------------------------------------------------------------------
        # Korrekte Implementierung über die Residuen/Pole und Strukturfunktion
        # Da dies ein RC-Netzwerk ist, ist die direkte Koeffizientenmethode stabiler. Wir kehren zur Koeffizientenmethode zurück, aber vereinfacht:
        # ----------------------------------------------------------------------
        
        RthCauer = []
        CthCauer = []
        
        # Y(s) = Q(s) / P(s)
        P_k = P_coeffs  # Zähler P(s)
        Q_k = Q_coeffs  # Nenner Q(s)
        
        # Y(s) = Q(s) / P(s) (Typ II: Parallel-C, Serie-R)
        # 1/Z(s) = Y(s) = c1*s + 1/Z1(s)
        # Z1(s) = r1 + 1/Y2(s)
        
        # Start mit Admittanz Y(s) = Q(s) / P(s)
        Y_num = Q_k
        Y_den = P_k
        
        for k in range(N):
            # 1. Schritt: Bestimme c_{k+1} aus Y_k(s)
            # c_{k+1} = lim_{s->inf} Y_k(s) / s
            
            # Koeffizient des höchsten s-Terms in Y_num (Grad N-k+1)
            num_high = Y_num[0]
            # Koeffizient des höchsten s-Terms in Y_den (Grad N-k)
            den_high = Y_den[0] 
            
            # c_i = num_high / den_high (der s-Term)
            c_i = num_high / den_high
            CthCauer.append(c_i)
            
            # Subtraktionsschritt: Y_num_new = Y_num - c_i * s * Y_den
            # Multipliziere Y_den mit c_i * s: [c_i*d_0, c_i*d_1, ..., 0]
            Y_den_mult_s = np.pad(Y_den * c_i, (0, 1), 'constant')
            
            # Subtraktion. Y_num ist um einen Grad höher als Y_den_mult_s
            Y_num_new = Y_num - Y_den_mult_s
            
            # Eliminiere führende Nullen in Y_num_new
            # Der höchste Koeffizient sollte Null sein, also bei Index 1 beginnen
            Y_num_new = Y_num_new[1:] 

            
            # Nächste Impedanz: Z_{k+1}(s) = Y_den / Y_num_new
            Z_num = Y_den
            Z_den = Y_num_new
            
            # Eliminiere führende Nullen in Z_num und Z_den (sollte nicht nötig sein)
            Z_num = Z_num[np.nonzero(Z_num)]
            Z_den = Z_den[np.nonzero(Z_den)]
            
            if len(Z_num) == 0 or len(Z_den) == 0:
                break

            # 2. Schritt: Bestimme r_{k+1} aus Z_{k+1}(s)
            # r_{k+1} = lim_{s->inf} Z_{k+1}(s)
            
            # Koeffizient des höchsten s-Terms in Z_num (Grad N-k)
            num_high = Z_num[0]
            # Koeffizient des höchsten s-Terms in Z_den (Grad N-k)
            den_high = Z_den[0]
            
            # r_i = num_high / den_high
            r_i = num_high / den_high
            RthCauer.append(r_i)
            
            # Subtraktionsschritt: Z_num_new = Z_num - r_i * Z_den
            Z_num_new = Z_num - r_i * Z_den
            
            # Eliminiere führende Nullen in Z_num_new
            Z_num_new = Z_num_new[1:] 

            # Nächste Admittanz: Y_{k+2}(s) = Z_den / Z_num_new
            Y_num = Z_den
            Y_den = Z_num_new

            # Eliminiere führende Nullen
            Y_num = Y_num[np.nonzero(Y_num)]
            Y_den = Y_den[np.nonzero(Y_den)]
            
            if len(Y_num) == 0 or len(Y_den) == 0:
                break

        # Da Cauer-II (Serien-R, Parallel-C) die Konvention ist:
        # RthCauer sind die Serienwiderstände, CthCauer sind die Parallelkapazitäten.
        return np.array(RthCauer), np.array(CthCauer)

    def cauer2foster_transform(self, RthCauer, CthCauer):
        """
        Transformiert die Parameter eines Cauer-RC-Leiternetzwerks (Typ II) in die 
        Parameter eines Foster-RC-Netzwerks (Typ I) mithilfe der Partialbruchzerlegung.

        Cauer Type II: Kette aus Parallelkapazitäten CthCauer und Serienwiderständen RthCauer.
        Foster Type I: Summe von parallel geschalteten R/C-Gliedern.

        Args:
            RthCauer (list oder numpy.array): Serienwiderstände [r1, r2, ...] des Cauer-Netzwerks.
            CthCauer (list oder numpy.array): Parallelkapazitäten [c1, c2, ...] des Cauer-Netzwerks.

        Returns:
            tuple: (RthFoster, CthFoster), Widerstände und Kapazitäten des Foster-Netzwerks.
                RthFoster = [R1, R2, ...] (Serienwiderstände in den parallelen Ästen)
                CthFoster = [C1, C2, ...] (Kapazitäten in den parallelen Ästen)
                
        Raises:
            ValueError: Wenn die Anzahl der R- und C-Elemente nicht übereinstimmt.
        """
        RthCauer = np.array(RthCauer, dtype=float)
        CthCauer = np.array(CthCauer, dtype=float)

        if len(RthCauer) != len(CthCauer):
            raise ValueError("Die Anzahl der Cauer-Widerstände und Kapazitäten muss übereinstimmen.")

        N = len(RthCauer)
        if N == 0:
            return [], []

        # 1. Bestimmung der rationalen Impedanzfunktion Z(s) = P(s) / Q(s)
        # Z(s) wird durch die Kettenbruch-Darstellung gegeben:
        # Z(s) = 1 / Y(s)
        # Y(s) = c1*s + 1 / (r1 + 1 / (c2*s + 1 / (r2 + ...)))

        # Wir verwenden einen iterativen Algorithmus, um die Zähler- und 
        # Nennerpolynome P(s) und Q(s) von Z(s) = P/Q zu bestimmen.
        
        # Der Algorithmus verwendet die Rekursionsformel für Kettenbrüche:
        # Z_k = N_k / D_k
        # N_k = a_k * N_{k-1} + N_{k-2}
        # D_k = a_k * D_{k-1} + D_{k-2}
        # a_k sind die Elemente des Kettenbruchs (c_i*s oder r_i).

        # Initialisierung für den Kettenbruch-Algorithmus:
        # Zähler-Polynome (P) und Nenner-Polynome (Q)
        P_prev = np.array([1.0])
        Q_prev = np.array([0.0])
        P_curr = np.array([0.0])
        Q_curr = np.array([1.0])

        for i in range(N):
            # 1. Schritt: Parallel-Kapazität c_i
            # Element a_i = c_i * s
            c_i = CthCauer[i]
            
            P_next = np.polyadd(np.pad(c_i * P_curr, (0, 1), 'constant'), P_prev)
            Q_next = np.polyadd(np.pad(c_i * Q_curr, (0, 1), 'constant'), Q_prev)
            
            P_prev, Q_prev = P_curr, Q_curr
            P_curr, Q_curr = P_next, Q_next
            
            # 2. Schritt: Serien-Widerstand r_i
            # Element a_i = r_i
            r_i = RthCauer[i]
            
            P_next = np.polyadd(r_i * P_curr, P_prev)
            Q_next = np.polyadd(r_i * Q_curr, Q_prev)
            
            P_prev, Q_prev = P_curr, Q_curr
            P_curr, Q_curr = P_next, Q_next

        # Die finale Impedanz ist Z(s) = N / D, wobei N = P_curr, D = Q_curr.
        # Da wir die Admittanz Y(s) = 1/Z(s) = D/N als Kettenbruch dargestellt haben, 
        # ist die finale Impedanz Z(s) = P_prev / Q_prev.
        # Z(s) = P(s) / Q(s)
        P_coeffs = P_prev
        Q_coeffs = Q_prev

        # Korrektur der Polynomgrade (führende Nullen entfernen)
        P_coeffs = np.trim_zeros(P_coeffs, 'f')
        Q_coeffs = np.trim_zeros(Q_coeffs, 'f')

        # 2. Partialbruchzerlegung von Z(s) = P(s) / Q(s)
        # Z(s) = R_inf + sum_{i=1}^{N} [ R_i / (s - p_i) ]
        # Für RC-Netzwerke gilt R_inf = 0, da deg(P) < deg(Q)
        
        # Verwende scipy.signal.residue für die Partialbruchzerlegung:
        # (r, p, k) = residue(P_coeffs, Q_coeffs)
        # r: Residuen R_i
        # p: Pole p_i
        # k: Konstante K (wieder R_inf)
        
        # SciPy erwartet die Polynome in absteigender Reihenfolge der Potenzen.
        r_residues, p_poles, k_constant = signal.residue(P_coeffs, Q_coeffs)

        # 3. Bestimmung der Foster-Parameter
        
        # Foster-Typ I Impedanz: Z(s) = sum_{i=1}^{N} [ R_i / (1 + s * R_i * C_i) ]
        # Diese Form ist äquivalent zu: Z(s) = sum_{i=1}^{N} [ R_i / (R_i*C_i * (s + 1/(R_i*C_i))) ]
        # Äquivalent zur Residuenform: Z(s) = sum_{i=1}^{N} [ Residuum_i / (s - Pole_i) ]
        
        # Pole p_i:
        # p_i = -1 / (R_i * C_i)  =>  R_i * C_i = -1 / p_i
        
        # Residuen r_residues:
        # r_residues[i] = R_i / (R_i * C_i) = 1 / C_i 
        # Achtung: Die Residuen für passive RC-Netzwerke sind R_i / (R_i*C_i) * (R_i*C_i) ?? Nein.
        # Residuum R_i_foster ist gleich der Residue r_residues[i] multipliziert mit -1/p_i
        
        # Korrekte Beziehung:
        # Z(s) = sum [ R_i / (1 + s*tau_i) ] = sum [ (R_i/tau_i) / (s + 1/tau_i) ]
        # Wobei tau_i = R_i * C_i.
        
        # Residuum r_residue[i] = R_i / tau_i
        # Pol p_i = -1 / tau_i
        
        # RthFoster: R_i = r_residue[i] / (1 / tau_i) = r_residue[i] / (-p_i)
        # CthFoster: C_i = tau_i / R_i = (-1 / p_i) / R_i
        
        RthFoster = r_residues / (-p_poles)
        CthFoster = 1.0 / r_residues 
        # Überprüfung: R_i * C_i = (r_res / -p) * (1 / r_res) = 1 / (-p) = tau_i. Korrekt!

        # Der Foster-Widerstand R_i ist immer reell und positiv.
        # Der Foster-Kondensator C_i ist immer reell und positiv.
        
        # Da die Pole p_i für RC-Netzwerke negativ sind (reelle, einfache Pole auf der negativen Achse), 
        # ist -p_i positiv, und RthFoster und CthFoster sind positiv.
        
        return RthFoster.real, CthFoster.real

    def report_peaks_to_console(self, peaks):
        outp = ""
        print(f"Deconvolvable to {len(peaks)} peaks")
        for peak in peaks:
            outp = outp + f"{self.z[peak]:.4e};{self.deconvolved[peak]:.4e};"
        print(outp)
        return

    # def add_deconv_tau_output_plot(self):
    #     lines = [
    #             {'x_data': self.z[:-1],
    #              'y_data': self.deconvolved,
    #              'label': f"Deconvolved with {self.iterations} Iterations",
    #              'axis': 0}]

    #     return ud_plot.UttaPlotConfiguration(plot_type='line',
    #                                          data=lines,
    #                                          x_label='Tau / [s]',
    #                                          y_label='Zth / [K/W]',
    #                                          title='Deconvolved Spectrum')
 
    # def add_zth_deconvolution_error_plot(self):
    #     lines = [
    #             {'x_data': self.z,
    #              'y_data': self.zth_deconvolved - self.a_z,
    #              'label': f"Delta Zth {self.iterations} Iterations",
    #              'axis': 0}]

    #     return ud_plot.UttaPlotConfiguration(plot_type='line',
    #                                          data=lines,
    #                                          x_label='Tau / [s]',
    #                                          y_label='Thermal Impedance / [K/W]',
    #                                          title='Deconvolved Thermal Impedance Error')

    # def add_deconv_zth_output_plot(self):
    #     lines = [{'x_data': np.exp(self.z),
    #               'y_data': self.zth_deconvolved,
    #               'label': f"Reconstructed Zth {self.iterations} Iterations",
    #               'axis': 0},
    #               {'x_data': np.exp(self.z),
    #               'y_data': self.a_z,
    #               'label': "Input Zth Curve",
    #               'axis': 0}]

    #     return ud_plot.UttaPlotConfiguration(plot_type='line',
    #                                          x_scale='log',
    #                                          #y_scale='log',
    #                                          data=lines,
    #                                          x_label='Time / [s]',
    #                                          y_label='Thermal Impedance / [K/W]',
    #                                          title='Thermal Impedance')


    # def add_dadz_deconv_output_plot(self):
    #     iterations = 1000
    #     lines = [
    #             {'x_data': self.z,
    #              'y_data': self.dadz_deconvolved,
    #              'label': f"da/dz {iterations} Iterations",
    #              'axis': 0}]

    #     return ud_plot.UttaPlotConfiguration(plot_type='line',
    #                                          data=lines,
    #                                          x_label='Tau / [s]',
    #                                          y_label='A.U',
    #                                          title='da/dz')

    # def add_dadz_deconv_error_plot(self):
    #     iterations = 1000
    #     lines = [
    #             {'x_data': self.z[:-1],
    #              'y_data': self.dadz - self.dadz_deconvolved[:-1],
    #              'label': f"Delta da/dz {iterations} Iterations",
    #              'axis': 0}]

    #     return ud_plot.UttaPlotConfiguration(plot_type='line',
    #                                          data=lines,
    #                                          x_label='Tau / [s]',
    #                                          y_label='A.U',
    #                                          title='da/dz Error')

    # def add_reference_deconv_output_plot(self):
    #     iterations = 1000
    #     lines = [
    #             {'x_data': self.z[:-1],
    #              'y_data': self.ref_deconv,
    #              'label': f"Reference deconv with {iterations} Iterations",
    #              'axis': 0}]

    #     return ud_plot.UttaPlotConfiguration(plot_type='line',
    #                                          data=lines,
    #                                          x_label='Tau / [s]',
    #                                          y_label='A.U',
    #                                          title='Reference Deconvolution (1K/W & 1Ws/K)')
