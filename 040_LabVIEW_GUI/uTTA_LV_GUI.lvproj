<?xml version='1.0' encoding='UTF-8'?>
<Project Type="Project" LVVersion="21008000">
	<Property Name="NI.LV.All.SourceOnly" Type="Bool">false</Property>
	<Property Name="NI.Project.Description" Type="Str"></Property>
	<Item Name="My Computer" Type="My Computer">
		<Property Name="IOScan.Faults" Type="Str"></Property>
		<Property Name="IOScan.NetVarPeriod" Type="UInt">100</Property>
		<Property Name="IOScan.NetWatchdogEnabled" Type="Bool">false</Property>
		<Property Name="IOScan.Period" Type="UInt">10000</Property>
		<Property Name="IOScan.PowerupMode" Type="UInt">0</Property>
		<Property Name="IOScan.Priority" Type="UInt">9</Property>
		<Property Name="IOScan.ReportModeConflict" Type="Bool">true</Property>
		<Property Name="IOScan.StartEngineOnDeploy" Type="Bool">false</Property>
		<Property Name="NI.SortType" Type="Int">3</Property>
		<Property Name="server.app.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.control.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="server.tcp.enabled" Type="Bool">false</Property>
		<Property Name="server.tcp.port" Type="Int">0</Property>
		<Property Name="server.tcp.serviceName" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.tcp.serviceName.default" Type="Str">My Computer/VI Server</Property>
		<Property Name="server.vi.callsEnabled" Type="Bool">true</Property>
		<Property Name="server.vi.propertiesEnabled" Type="Bool">true</Property>
		<Property Name="specify.custom.address" Type="Bool">false</Property>
		<Item Name="uTTA" Type="Folder">
			<Item Name="uTTA_SubVi" Type="Folder">
				<Item Name="MEAS" Type="Folder">
					<Item Name="Sampling" Type="Folder">
						<Item Name="uTTA_GetSamplingSettings.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GetSamplingSettings.vi"/>
						<Item Name="uTTA_SetFastSamplerate.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetFastSamplerate.vi"/>
						<Item Name="uTTA_GetMaxMultiplier.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GetMaxMultiplier.vi"/>
						<Item Name="uTTA_SetMaxMultiplier.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetMaxMultiplier.vi"/>
					</Item>
					<Item Name="Timing" Type="Folder">
						<Item Name="uTTA_SetCoolingTime.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetCoolingTime.vi"/>
						<Item Name="uTTA_GetTimingSettings.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GetTimingSettings.vi"/>
						<Item Name="uTTA_SetHeatingTime.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetHeatingTime.vi"/>
						<Item Name="uTTA_SetPreHeatingTime.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetPreHeatingTime.vi"/>
					</Item>
					<Item Name="uTTA_SetDUT_Name.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetDUT_Name.vi"/>
					<Item Name="uTTA_SetCH_Description.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetCH_Description.vi"/>
					<Item Name="uTTA_SetMeasure.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetMeasure.vi"/>
				</Item>
				<Item Name="SYSTEM" Type="Folder">
					<Item Name="uTTA_GetPGAGain.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GetPGAGain.vi"/>
					<Item Name="uTTA_GetPSU.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GetPSU.vi"/>
					<Item Name="uTTA_SwitchGD_Power.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SwitchGD_Power.vi"/>
					<Item Name="uTTA_GetPWSTG.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GetPWSTG.vi"/>
					<Item Name="uTTA_GetPWUVLO.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GetPWUVLO.vi"/>
					<Item Name="uTTA_SetCALSamplerate.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetCALSamplerate.vi"/>
					<Item Name="uTTA_SetMode.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetMode.vi"/>
					<Item Name="uTTA_SetPGAGain.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SetPGAGain.vi"/>
					<Item Name="uTTA_SwitchPSU.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SwitchPSU.vi"/>
					<Item Name="uTTA_SwitchPWSTG.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SwitchPWSTG.vi"/>
				</Item>
				<Item Name="Flash_Memory" Type="Folder">
					<Item Name="uTTA_Memory_Writetest.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_Memory_Writetest.vi"/>
					<Item Name="uTTA_ReadFileFromMemory_Save.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_ReadFileFromMemory_Save.vi"/>
					<Item Name="uTTA_ReadDirectory.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_ReadDirectory.vi"/>
					<Item Name="uTTA_DeleteFile.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_DeleteFile.vi"/>
				</Item>
				<Item Name="CTL_uTTA_OperatingMode.ctl" Type="VI" URL="../uTTA/uTTA_Device_Driver/CTL_uTTA_OperatingMode.ctl"/>
				<Item Name="CTL_uTTA_SamplingSettings.ctl" Type="VI" URL="../uTTA/uTTA_Device_Driver/CTL_uTTA_SamplingSettings.ctl"/>
				<Item Name="CTL_uTTA_TimingSettings.ctl" Type="VI" URL="../uTTA/Postprocessing/CTL_uTTA_TimingSettings.ctl"/>
				<Item Name="CTL_uTTA_MeasurementStates.ctl" Type="VI" URL="../uTTA/uTTA_Device_Driver/CTL_uTTA_MeasurementStates.ctl"/>
				<Item Name="CTL_uTTA_MeasurementDataValues.ctl" Type="VI" URL="../uTTA/Postprocessing/CTL_uTTA_MeasurementDataValues.ctl"/>
				<Item Name="CTL_uTTA_PGA_Gain.ctl" Type="VI" URL="../uTTA/uTTA_Device_Driver/CTL_uTTA_PGA_Gain.ctl"/>
				<Item Name="uTTA_GetLiveMeasureStatus.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GetLiveMeasureStatus.vi"/>
				<Item Name="uTTA_Init.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_Init.vi"/>
				<Item Name="uTTA_FlushSerialBuffer.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_FlushSerialBuffer.vi"/>
				<Item Name="uTTA_OpenCOM.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_OpenCOM.vi"/>
				<Item Name="uTTA_CloseCOM.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_CloseCOM.vi"/>
				<Item Name="uTTA_SendQuery.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_SendQuery.vi"/>
				<Item Name="uTTA_Reset.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_Reset.vi"/>
				<Item Name="uTTA_CheckForErrors.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_CheckForErrors.vi"/>
				<Item Name="uTTA_GV_Serial_Monitor.vi" Type="VI" URL="../uTTA/uTTA_GV_Serial_Monitor.vi"/>
				<Item Name="uTTA_GenerateErrorClusters.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GenerateErrorClusters.vi"/>
				<Item Name="uTTA_LogSerial.vi" Type="VI" URL="../uTTA/uTTA_LogSerial.vi"/>
			</Item>
			<Item Name="Postprocessing" Type="Folder">
				<Item Name="SubVi" Type="Folder">
					<Item Name="uTTA_CutCoolingToSection.vi" Type="VI" URL="../uTTA/Postprocessing/uTTA_CutCoolingToSection.vi"/>
					<Item Name="Interpolate_Curve.vi" Type="VI" URL="../uTTA/Postprocessing/Interpolate_Curve.vi"/>
					<Item Name="Scale_DiodeTemp.vi" Type="VI" URL="../uTTA/Postprocessing/Scale_DiodeTemp.vi"/>
					<Item Name="uTTA_ReadCAL_File.vi" Type="VI" URL="../uTTA/Postprocessing/uTTA_ReadCAL_File.vi"/>
					<Item Name="uTTA_ParseT3rFile.vi" Type="VI" URL="../uTTA/Postprocessing/uTTA_ParseT3rFile.vi"/>
					<Item Name="uTTA_ScaleMeasurementData.vi" Type="VI" URL="../uTTA/Postprocessing/uTTA_ScaleMeasurementData.vi"/>
					<Item Name="CTL_uTTA_MeasurementData.ctl" Type="VI" URL="../uTTA/Postprocessing/CTL_uTTA_MeasurementData.ctl"/>
					<Item Name="uTTA_MetaData.ctl" Type="VI" URL="../uTTA/Postprocessing/uTTA_MetaData.ctl"/>
					<Item Name="uTTA_Read_T3rFile.vi" Type="VI" URL="../uTTA/Postprocessing/uTTA_Read_T3rFile.vi"/>
					<Item Name="ArrayFindClosestValue.vi" Type="VI" URL="../uTTA/Postprocessing/ArrayFindClosestValue.vi"/>
					<Item Name="CTRL_DUT_SETTINGS.ctl" Type="VI" URL="../uTTA/Postprocessing/CTRL_DUT_SETTINGS.ctl"/>
				</Item>
				<Item Name="uTTA_Read_File_UI.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_Read_File_UI.vi"/>
				<Item Name="uTTA_PostProcessing_V2.vi" Type="VI" URL="../uTTA/uTTA_PostProcessing_V2.vi"/>
				<Item Name="uTTA_TDMS_Viewer.vi" Type="VI" URL="../uTTA/uTTA_TDMS_Viewer.vi"/>
				<Item Name="uTTA_FindIllegalCharacters.vi" Type="VI" URL="../uTTA/uTTA_FindIllegalCharacters.vi"/>
			</Item>
			<Item Name="Calibration" Type="Folder">
				<Item Name="SubVi" Type="Folder">
					<Item Name="uTTA_GetCAL_Output.vi" Type="VI" URL="../uTTA/uTTA_Device_Driver/uTTA_GetCAL_Output.vi"/>
					<Item Name="Read_K2000_ValuesAveraged.vi" Type="VI" URL="../uTTA/Calibration/Read_K2000_ValuesAveraged.vi"/>
					<Item Name="uTTA_CalReadData.vi" Type="VI" URL="../uTTA/uTTA_CalReadData.vi"/>
					<Item Name="Read_uTTA_CalibrationFile.vi" Type="VI" URL="../uTTA/Calibration/Read_uTTA_CalibrationFile.vi"/>
					<Item Name="Write_uTTA_CalibrationFile.vi" Type="VI" URL="../uTTA/Calibration/Write_uTTA_CalibrationFile.vi"/>
				</Item>
				<Item Name="uTTA_Calibration.vi" Type="VI" URL="../uTTA/uTTA_Calibration.vi"/>
				<Item Name="uTTA_CreateCAL_File.vi" Type="VI" URL="../uTTA/Postprocessing/uTTA_CreateCAL_File.vi"/>
			</Item>
		</Item>
		<Item Name="uTTA_Main.vi" Type="VI" URL="../uTTA/uTTA_Main.vi"/>
		<Item Name="Dependencies" Type="Dependencies">
			<Item Name="user.lib" Type="Folder">
				<Item Name="String to 1D Array__ogtk.vi" Type="VI" URL="/&lt;userlib&gt;/_OpenG.lib/string/string.llb/String to 1D Array__ogtk.vi"/>
			</Item>
			<Item Name="vi.lib" Type="Folder">
				<Item Name="BuildHelpPath.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/BuildHelpPath.vi"/>
				<Item Name="Check if File or Folder Exists.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/libraryn.llb/Check if File or Folder Exists.vi"/>
				<Item Name="Check Special Tags.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Check Special Tags.vi"/>
				<Item Name="Clear Errors.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Clear Errors.vi"/>
				<Item Name="Convert property node font to graphics font.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Convert property node font to graphics font.vi"/>
				<Item Name="Details Display Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Details Display Dialog.vi"/>
				<Item Name="DialogType.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/DialogType.ctl"/>
				<Item Name="DialogTypeEnum.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/DialogTypeEnum.ctl"/>
				<Item Name="Error Cluster From Error Code.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error Cluster From Error Code.vi"/>
				<Item Name="Error Code Database.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Error Code Database.vi"/>
				<Item Name="ErrWarn.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/ErrWarn.ctl"/>
				<Item Name="eventvkey.ctl" Type="VI" URL="/&lt;vilib&gt;/event_ctls.llb/eventvkey.ctl"/>
				<Item Name="ex_CorrectErrorChain.vi" Type="VI" URL="/&lt;vilib&gt;/express/express shared/ex_CorrectErrorChain.vi"/>
				<Item Name="Find Tag.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Find Tag.vi"/>
				<Item Name="Format Message String.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Format Message String.vi"/>
				<Item Name="General Error Handler Core CORE.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/General Error Handler Core CORE.vi"/>
				<Item Name="General Error Handler.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/General Error Handler.vi"/>
				<Item Name="Get File Extension.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/libraryn.llb/Get File Extension.vi"/>
				<Item Name="Get String Text Bounds.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Get String Text Bounds.vi"/>
				<Item Name="Get Text Rect.vi" Type="VI" URL="/&lt;vilib&gt;/picture/picture.llb/Get Text Rect.vi"/>
				<Item Name="GetHelpDir.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/GetHelpDir.vi"/>
				<Item Name="GetRTHostConnectedProp.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/GetRTHostConnectedProp.vi"/>
				<Item Name="Is Path and Not Empty.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/Is Path and Not Empty.vi"/>
				<Item Name="Longest Line Length in Pixels.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Longest Line Length in Pixels.vi"/>
				<Item Name="LVBoundsTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVBoundsTypeDef.ctl"/>
				<Item Name="LVPointTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVPointTypeDef.ctl"/>
				<Item Name="LVRectTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVRectTypeDef.ctl"/>
				<Item Name="NI_AALBase.lvlib" Type="Library" URL="/&lt;vilib&gt;/Analysis/NI_AALBase.lvlib"/>
				<Item Name="NI_AALPro.lvlib" Type="Library" URL="/&lt;vilib&gt;/Analysis/NI_AALPro.lvlib"/>
				<Item Name="NI_FileType.lvlib" Type="Library" URL="/&lt;vilib&gt;/Utility/lvfile.llb/NI_FileType.lvlib"/>
				<Item Name="NI_PackedLibraryUtility.lvlib" Type="Library" URL="/&lt;vilib&gt;/Utility/LVLibp/NI_PackedLibraryUtility.lvlib"/>
				<Item Name="Not Found Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Not Found Dialog.vi"/>
				<Item Name="Search and Replace Pattern.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Search and Replace Pattern.vi"/>
				<Item Name="Set Bold Text.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Set Bold Text.vi"/>
				<Item Name="Set String Value.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Set String Value.vi"/>
				<Item Name="Simple Error Handler.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Simple Error Handler.vi"/>
				<Item Name="subFile Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/express/express input/FileDialogBlock.llb/subFile Dialog.vi"/>
				<Item Name="subTimeDelay.vi" Type="VI" URL="/&lt;vilib&gt;/express/express execution control/TimeDelayBlock.llb/subTimeDelay.vi"/>
				<Item Name="TagReturnType.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/TagReturnType.ctl"/>
				<Item Name="Three Button Dialog CORE.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Three Button Dialog CORE.vi"/>
				<Item Name="Three Button Dialog.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Three Button Dialog.vi"/>
				<Item Name="Trim Whitespace.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/Trim Whitespace.vi"/>
				<Item Name="VISA Configure Serial Port" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/VISA Configure Serial Port"/>
				<Item Name="VISA Configure Serial Port (Instr).vi" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/VISA Configure Serial Port (Instr).vi"/>
				<Item Name="VISA Configure Serial Port (Serial Instr).vi" Type="VI" URL="/&lt;vilib&gt;/Instr/_visa.llb/VISA Configure Serial Port (Serial Instr).vi"/>
				<Item Name="whitespace.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/error.llb/whitespace.ctl"/>
				<Item Name="cfis_Replace Percent Code.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/cfis_Replace Percent Code.vi"/>
				<Item Name="cfis_Reverse Scan From String For Integer.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/cfis_Reverse Scan From String For Integer.vi"/>
				<Item Name="cfis_Get File Extension Without Changing Case.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/cfis_Get File Extension Without Changing Case.vi"/>
				<Item Name="cfis_Split File Path Into Three Parts.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/cfis_Split File Path Into Three Parts.vi"/>
				<Item Name="Create File with Incrementing Suffix.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/file.llb/Create File with Incrementing Suffix.vi"/>
				<Item Name="Less Comparable.lvclass" Type="LVClass" URL="/&lt;vilib&gt;/Comparison/Less/Less Comparable/Less Comparable.lvclass"/>
				<Item Name="Less Functor.lvclass" Type="LVClass" URL="/&lt;vilib&gt;/Comparison/Less/Less Functor/Less Functor.lvclass"/>
				<Item Name="Less.vim" Type="VI" URL="/&lt;vilib&gt;/Comparison/Less.vim"/>
				<Item Name="Sort 1D Array Core.vim" Type="VI" URL="/&lt;vilib&gt;/Array/Helpers/Sort 1D Array Core.vim"/>
				<Item Name="Sort 1D Array.vim" Type="VI" URL="/&lt;vilib&gt;/Array/Sort 1D Array.vim"/>
				<Item Name="LVPoint32TypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVPoint32TypeDef.ctl"/>
				<Item Name="NI_TDMS File Viewer.lvlib" Type="Library" URL="/&lt;vilib&gt;/Utility/TDMS File Viewer/NI_TDMS File Viewer.lvlib"/>
				<Item Name="LVRowAndColumnTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVRowAndColumnTypeDef.ctl"/>
				<Item Name="Set Cursor (Icon Pict).vi" Type="VI" URL="/&lt;vilib&gt;/Utility/cursorutil.llb/Set Cursor (Icon Pict).vi"/>
				<Item Name="Set Cursor (Cursor ID).vi" Type="VI" URL="/&lt;vilib&gt;/Utility/cursorutil.llb/Set Cursor (Cursor ID).vi"/>
				<Item Name="Set Cursor.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/cursorutil.llb/Set Cursor.vi"/>
				<Item Name="Unset Busy.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/cursorutil.llb/Unset Busy.vi"/>
				<Item Name="Progress Bar Dialog.lvclass" Type="LVClass" URL="/&lt;vilib&gt;/ProgressBar/Progress Bar Dialog.lvclass"/>
				<Item Name="Remove Duplicates From 1D Array.vim" Type="VI" URL="/&lt;vilib&gt;/Array/Remove Duplicates From 1D Array.vim"/>
				<Item Name="NI_Data Type.lvlib" Type="Library" URL="/&lt;vilib&gt;/Utility/Data Type/NI_Data Type.lvlib"/>
				<Item Name="Set Busy.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/cursorutil.llb/Set Busy.vi"/>
				<Item Name="LVCursorListTypeDef.ctl" Type="VI" URL="/&lt;vilib&gt;/Utility/miscctls.llb/LVCursorListTypeDef.ctl"/>
				<Item Name="NI_PtbyPt.lvlib" Type="Library" URL="/&lt;vilib&gt;/ptbypt/NI_PtbyPt.lvlib"/>
				<Item Name="8.6CompatibleGlobalVar.vi" Type="VI" URL="/&lt;vilib&gt;/Utility/config.llb/8.6CompatibleGlobalVar.vi"/>
				<Item Name="NI_LVConfig.lvlib" Type="Library" URL="/&lt;vilib&gt;/Utility/config.llb/NI_LVConfig.lvlib"/>
				<Item Name="Space Constant.vi" Type="VI" URL="/&lt;vilib&gt;/dlg_ctls.llb/Space Constant.vi"/>
			</Item>
			<Item Name="lvanlys.dll" Type="Document" URL="/&lt;resource&gt;/lvanlys.dll"/>
			<Item Name="AR488_Init.vi" Type="VI" URL="../Drivers/AR488/AR488_Init.vi"/>
			<Item Name="AR488_Set_Address.vi" Type="VI" URL="../Drivers/AR488/AR488_Set_Address.vi"/>
			<Item Name="AR488_Write.vi" Type="VI" URL="../Drivers/AR488/AR488_Write.vi"/>
			<Item Name="AR488_Read.vi" Type="VI" URL="../Drivers/AR488/AR488_Read.vi"/>
		</Item>
		<Item Name="Build Specifications" Type="Build"/>
	</Item>
</Project>
