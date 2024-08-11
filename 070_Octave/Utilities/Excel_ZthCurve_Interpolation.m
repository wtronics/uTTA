%
% Excel_ZthCurve_Interpolation.m
%
% Created on: 11.08.2024
% Author: wtronics
%
% This Matlab / Octave program can be used to harmonize Zth curves from different sources.
% All Zth-curves within the Excel input document are imported and interpolated to a common time base.
% Note: The whole Excel document should only contain Zth curves where the first column represents the time and the second column the thermal impedance.
% All worksheets of the Excel document are imported and interpolated. Each Zth curve is then exported to a dedicated CSV-File.
% In case the input Zth curve does not fully fit the output timebase (shorter timebase than the output) the output will be NA.
%


close all;
clear all;
clc;

% Settings
Tstart = 1e-6;        % start time for interpolation (1µs)
Tend = 1e4;           % end time for interpolation (10000s)
StepsPerDecade = 10;  % Steps per decade (10) e.g. 10 values between 1 and 10 whereby 10 is not included in this intervall.
RemoveNA = 0;         % Setting to remove NA values from the output file
                      % (e.g. when the set start time is 1µs and the input data start at 10µs the first 10 samples will be NA.
                      % These 10 samples can be removed by setting this option to 1).

% Create a logarithmic timebase
Timebase = power(10,linspace(log10(Tstart),log10(Tend), (log10(Tend)-log10(Tstart))* StepsPerDecade+1));

% File selection dialog for input data
[FileName, FilePath] = uigetfile("*.xlsx");

if (ischar(FileName))  % Make sure the filename is not empty
  PathFileName = strcat(FilePath, FileName);

  % Get a file info and the names of all worksheets.
  [FileInfo,WksInfo] = xlsfinfo(PathFileName)

  % run through all worksheets and do the interpolation
  for WksIdx = 1:length(WksInfo)
    WksName = char(WksInfo(WksIdx,1))
    Data = xlsread(PathFileName,WksName);

    InTime = Data(:,1);
    InZth = Data(:,2);
    loglog(InTime, InZth,"displayname", WksName)
    hold on

    Zth_Interpol = interp1(InTime,InZth, Timebase,"spline");
    loglog(Timebase, Zth_Interpol,"displayname", strcat(WksName, " Interpolated"))
    legend


    OutData = [Timebase' Zth_Interpol'];

    if RemoveNA = 1
      for OutIdx = length(OutData):-1:1
        if isna(OutData(OutIdx,2))
          OutData(OutIdx,:) = [];
        endif
      endfor
    endif
    % Create an automatic file name for the interpolated output and store results there
    Outfilename = strcat(FilePath, strrep(FileName,".xlsx",strcat("_", WksName, "_interpolated.csv")));
    dlmwrite(Outfilename, OutData, ",")

  endfor
endif
