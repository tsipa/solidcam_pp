<?xml version="1.0"?>
<VcControl Version="9.6" Unit="millimeter">
  <Information>
    <InfoUserName>Ts</InfoUserName>
    <InfoDateTime>Tue Jan  6 18:31:05 2026</InfoDateTime>
    <InfoVericutVersion>9.6</InfoVericutVersion>
    <InfoBuildDate>September 10, 2025 </InfoBuildDate>
    <InfoLibraryDate>06/23/25</InfoLibraryDate>
  </Information>
  <COMMENT>Library File: sin840d.ctl, Revision 9.6.14, Issued: Wed Aug 06 15:30:31 2025</COMMENT>
  <ControlInitFile File="${CGTECH_INSTALL}\library\sin840d.def" />
  <ConstSurfSpeed Rapid="off" MaxRPM="1000" />
  <Sync Method="none">
  </Sync>
  <Subroutines>
    <File>${CGTECH_INSTALL}\library\sin840d.spf</File>
    <File>${CGTECH_INSTALL}\library\sin840d.vcsub</File>
    <File>${CGTECH_INSTALL}\library\sin840d.xsub</File>
  </Subroutines>
  <Words>
    <Word Name="&quot;" Type="sin840D_quoted_text">
    </Word>
    <Word Name="$$" Type="skip">
    </Word>
    <Word Name="%" Type="skip">
    </Word>
    <Word Name="%L" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="%MPF" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="%SPF" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="%_N_" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="&amp;" Type="ignore">
    </Word>
    <Word Name="&apos;" Type="ignore">
    </Word>
    <Word Name="&apos;B" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="QuoteCondBINWord"/>
    </Word>
    <Word Name="&apos;H" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="QuoteCondHEXWord"/>
    </Word>
    <Word Name="&apos;O" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="QuoteCondOCTWord"/>
    </Word>
    <Word Name="(" Type="left_precedence">
    </Word>
    <Word Name="(I/" Type="skip">
    </Word>
    <Word Name=")" Type="right_precedence">
    </Word>
    <Word Name="*" Type="multiplication">
    </Word>
    <Word Name="+" Type="addition">
    </Word>
    <Word Name="," Type="separator">
    </Word>
    <Word Name="-" Type="subtraction">
    </Word>
    <Word Name="/" Type="division">
    </Word>
    <Word Name="//" Type="skip">
    </Word>
    <Word Name=":" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensCondColon"/>
    </Word>
    <Word Name=";" Type="begin_comment">
    </Word>
    <Word Name="&lt;" Type="less_than">
    </Word>
    <Word Name="&lt;&lt;" Type="concatenate">
    </Word>
    <Word Name="&lt;=" Type="less_equal">
    </Word>
    <Word Name="&lt;&gt;" Type="not_equal">
    </Word>
    <Word Name="=" Type="assignment">
    </Word>
    <Word Name="==" Type="equal">
    </Word>
    <Word Name="=EOF=" Type="skip">
    </Word>
    <Word Name="&gt;" Type="greater_than">
    </Word>
    <Word Name="&gt;=" Type="greater_equal">
    </Word>
    <Word Name="[" Type="left_precedence">
    </Word>
    <Word Name="\N" Type="end_block">
    </Word>
    <Word Name="]" Type="right_precedence">
    </Word>
    <Word Name="^" Type="power">
    </Word>
    <Word Name="____" Type="ignore">
    </Word>
    <Word Name="||" Type="skip">
    </Word>
    <Word Name="A" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="A2" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="A3=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="1.8" MetricType="decimal" MetricFormat="1.8" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="ABS" Type="function_call">
      <Function Name="abs" Type="normal"/>
    </Word>
    <Word Name="AC" Type="function_call">
      <Function Name="AbsoluteDimension" Type="normal"/>
    </Word>
    <Word Name="ACCLIMA" Type="macro_call">
      <Value Type="list_alpha_numeric"/>
    </Word>
    <Word Name="ACN" Type="function_call">
      <Function Name="SiemensACN" Type="normal"/>
    </Word>
    <Word Name="ACOS" Type="function_call">
      <Function Name="acos_d" Type="normal"/>
    </Word>
    <Word Name="ACP" Type="function_call">
      <Function Name="SiemensACP" Type="normal"/>
    </Word>
    <Word Name="ACTBLOCNO" Type="ignore">
    </Word>
    <Word Name="ADIS" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="ADISPOS" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="ADISPOSA" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="ALF" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="AMIRROR" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="AN3=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="1.8" MetricType="decimal" MetricFormat="1.8" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="AND" Type="and">
    </Word>
    <Word Name="ANG" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="AP" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="APR" Type="begin_comment">
    </Word>
    <Word Name="APW" Type="begin_comment">
    </Word>
    <Word Name="AR" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="AROT" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ASCALE" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ASIN" Type="function_call">
      <Function Name="asin_d" Type="normal"/>
    </Word>
    <Word Name="ATAN" Type="function_call">
      <Function Name="atan_d" Type="normal"/>
    </Word>
    <Word Name="ATAN2" Type="function_call">
      <Function Name="atan2_d" Type="normal"/>
    </Word>
    <Word Name="ATRANS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="AX" Type="sind840D_AX">
    </Word>
    <Word Name="AXNAME" Type="function_call">
      <Function Name="SiemensAxName" Type="normal"/>
    </Word>
    <Word Name="AXSTRING" Type="function_call">
      <Function Name="SiemensAxString" Type="siemens_axis"/>
    </Word>
    <Word Name="AXTOSPI" Type="function_call">
      <Function Name="SiemensAXTOSPI" Type="normal"/>
    </Word>
    <Word Name="A_AND" Type="and">
    </Word>
    <Word Name="B" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="B2" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="B3=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="1.8" MetricType="decimal" MetricFormat="1.8" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="BLANK" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="BLOCK" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="BN3=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="1.8" MetricType="decimal" MetricFormat="1.8" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="BPARATAB" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="BRISK" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="BRISKA" Type="macro_call">
      <Value Type="list_alpha_numeric"/>
    </Word>
    <Word Name="BRPMTEST" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="BSPLINE" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="BTEXT" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="B_AND" Type="bitwise_and">
    </Word>
    <Word Name="B_NOT" Type="function_call">
      <Function Name="BitwiseNOT" Type="normal"/>
    </Word>
    <Word Name="B_OR" Type="bitwise_or">
    </Word>
    <Word Name="B_PROJECTION" Type="variable_name">
    </Word>
    <Word Name="B_XOR" Type="bitwise_xor">
    </Word>
    <Word Name="C" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="C2" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="C3=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="1.8" MetricType="decimal" MetricFormat="1.8" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="CALCDAT" Type="function_call">
      <Function Name="CalcCircleData" Type="siemens_intersec"/>
    </Word>
    <Word Name="CALL" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="CANCEL" Type="macro_call">
      <Value Type="list_numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="CASE" Type="S840D_case">
    </Word>
    <Word Name="CDOF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CFC" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CFIN" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CFINE" Type="function_call">
      <Function Name="SiemensCFINE" Type="siemens_frame"/>
    </Word>
    <Word Name="CFTCP" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CHANDATA" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="CHECKSUM" Type="ignore">
    </Word>
    <Word Name="CHF" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="CHIRON_TC_TYPE" Type="variable_name">
    </Word>
    <Word Name="CHR" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="CIP" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CLEARM" Type="macro_call">
      <Value Type="list_numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="CLEARM()" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CLOSE" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CMIRROR" Type="function_call">
      <Function Name="SiemensCMIRROR" Type="siemens_frame"/>
    </Word>
    <Word Name="CN3=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="1.8" MetricType="decimal" MetricFormat="1.8" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="COMPCAD" Type="ignore">
    </Word>
    <Word Name="CONNECT" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="CONNECT_TO" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="CONTPRON" Type="macro_call">
      <Value Type="text_string"/>
    </Word>
    <Word Name="COS" Type="function_call">
      <Function Name="cos_d" Type="normal"/>
    </Word>
    <Word Name="CP" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CR=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="CROT" Type="function_call">
      <Function Name="SiemensCROT" Type="siemens_frame"/>
    </Word>
    <Word Name="CROTS" Type="function_call">
      <Function Name="SiemensCROT" Type="siemens_frame"/>
    </Word>
    <Word Name="CRPL" Type="function_call">
      <Function Name="SiemensCRPL" Type="normal"/>
    </Word>
    <Word Name="CSCALE" Type="function_call">
      <Function Name="SiemensCSCALE" Type="siemens_frame"/>
    </Word>
    <Word Name="CT" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CTRANS" Type="function_call">
      <Function Name="SiemensCTRANS" Type="siemens_frame"/>
    </Word>
    <Word Name="CUT2D" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CUT2DF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CUT3DC" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CUT3DCC" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CUT3DCCD" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CUT3DF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CUT3DFF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CUT3DFS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="CYC_CUS" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="D" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="2.0" MetricType="decimal" MetricFormat="2.0" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="DC" Type="function_call">
      <Function Name="SiemensDC" Type="normal"/>
    </Word>
    <Word Name="DEF" Type="S840D_def">
    </Word>
    <Word Name="DEFINE" Type="S840D_define">
    </Word>
    <Word Name="DELETE" Type="sin840D_DELETE">
    </Word>
    <Word Name="DELOBJ" Type="ignore">
    </Word>
    <Word Name="DIAM90" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="DIAMCYCOF" Type="ignore">
    </Word>
    <Word Name="DIAMOF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="DIAMON" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="DISCL" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="DISPLOF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="DISR" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="DITRB" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="DIV" Type="div">
    </Word>
    <Word Name="DL" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="DL=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="DO" Type="macro_call">
      <Value Type="text_string"/>
    </Word>
    <Word Name="DOORS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="DRFOF" Type="begin_comment">
    </Word>
    <Word Name="DRIVE" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="DRIVEA" Type="macro_call">
      <Value Type="list_alpha_numeric"/>
    </Word>
    <Word Name="E" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="ELSE" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="ENDFOR" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ENDIF" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="ENDLOOP" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="ENDPROC" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ENDWHILE" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="EVERY" Type="macro_call">
      <Value Type="text_string"/>
    </Word>
    <Word Name="EX" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="ConstCondEXPWord"/>
    </Word>
    <Word Name="EXECSTRING" Type="execstring">
    </Word>
    <Word Name="EXECTAB" Type="macro_call">
      <Value Type="text_string"/>
    </Word>
    <Word Name="EXECUTE" Type="macro_call">
      <Value Type="text_string"/>
    </Word>
    <Word Name="EXP" Type="function_call">
      <Function Name="exp" Type="normal"/>
    </Word>
    <Word Name="EXTCALL" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="EXTERN" Type="begin_comment">
    </Word>
    <Word Name="F" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="FAD" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="FB" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="FEHLERBEHANDLUNG" Type="ignore">
    </Word>
    <Word Name="FFWOF" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="FFWON" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="FI" Type="var_name">
    </Word>
    <Word Name="FLIN" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="FLOOR" Type="function_call">
      <Function Name="floor" Type="normal"/>
    </Word>
    <Word Name="FNORM" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="FOR" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="FRC" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="FRCM" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="FROM" Type="macro_call">
      <Value Type="text_string"/>
    </Word>
    <Word Name="G" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensArrayCond"/>
    </Word>
    <Word Name="GD" Type="variable_name">
    </Word>
    <Word Name="GETT" Type="function_call">
      <Function Name="ToolIDToIndex" Type="normal"/>
    </Word>
    <Word Name="GETVARDIM" Type="function_call">
      <Function Name="GetVarDim" Type="normal"/>
    </Word>
    <Word Name="GETVARTYP" Type="function_call">
      <Function Name="GetVarTyp" Type="normal"/>
    </Word>
    <Word Name="GOTO" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="GOTOB" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="GOTOC" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="GOTOF" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="G_COLLET" Type="variable_name">
    </Word>
    <Word Name="H" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="3.0" MetricType="decimal" MetricFormat="3.0" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H51=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H52=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H53=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H54=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H55=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H56=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H57=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H58=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H61=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="H62=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="I" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="I1=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="IC" Type="function_call">
      <Function Name="IncrementalValue" Type="normal"/>
    </Word>
    <Word Name="ID" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="IDS" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="IF" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="INCH" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="INC_AP" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="INDEX" Type="function_call">
      <Function Name="INDEX" Type="normal"/>
    </Word>
    <Word Name="INIT" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="INTERSEC" Type="function_call">
      <Function Name="INTERSEC" Type="siemens_intersec"/>
    </Word>
    <Word Name="INVCCW" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="INVCW" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="INVFRAME" Type="function_call">
      <Function Name="SiemensINVFRAME" Type="siemens_frame"/>
    </Word>
    <Word Name="IP" Type="sin840D_IP">
    </Word>
    <Word Name="ISAXIS" Type="function_call">
      <Function Name="ISAXIS" Type="normal"/>
    </Word>
    <Word Name="ISFILE" Type="function_call">
      <Function Name="ISFILE" Type="normal"/>
    </Word>
    <Word Name="ISNUMBER" Type="function_call">
      <Function Name="ISNUMBER" Type="normal"/>
    </Word>
    <Word Name="ISVAR" Type="function_call">
      <Function Name="ISVAR" Type="normal"/>
    </Word>
    <Word Name="ITOR" Type="function_call">
      <Function Name="Round" Type="normal"/>
    </Word>
    <Word Name="J" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="J1=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="JERKA" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="JERKLIM" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="JERKLIMA" Type="macro_call">
      <Value Type="list_alpha_numeric"/>
    </Word>
    <Word Name="K" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="K1=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="LFOF" Type="ignore">
    </Word>
    <Word Name="LFON" Type="ignore">
    </Word>
    <Word Name="LFPOS" Type="ignore">
    </Word>
    <Word Name="LFTXT" Type="ignore">
    </Word>
    <Word Name="LFWP" Type="ignore">
    </Word>
    <Word Name="LIMS" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.0" MetricType="decimal" MetricFormat="4.0" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="LN" Type="function_call">
      <Function Name="ln" Type="normal"/>
    </Word>
    <Word Name="LOOP" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="M" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="4.0" MetricType="decimal" MetricFormat="4.0" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensArrayCond"/>
    </Word>
    <Word Name="MATCH" Type="function_call">
      <Function Name="INDEX" Type="normal"/>
    </Word>
    <Word Name="MAXVAL" Type="function_call">
      <Function Name="MAX" Type="normal"/>
    </Word>
    <Word Name="MB" Type="variable_name">
    </Word>
    <Word Name="MC13" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond"/>
    </Word>
    <Word Name="MCALL" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="MEAFRAME" Type="function_call">
      <Function Name="SiemensMEAFRAME" Type="siemens_mea_frame"/>
    </Word>
    <Word Name="MEAS" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="MESSEND" Type="ignore">
    </Word>
    <Word Name="METRIC" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="MI" Type="var_name">
    </Word>
    <Word Name="MINDEX" Type="function_call">
      <Function Name="MINDEX" Type="normal"/>
    </Word>
    <Word Name="MINVAL" Type="function_call">
      <Function Name="MIN" Type="normal"/>
    </Word>
    <Word Name="MIRROR" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="MOD" Type="mod">
    </Word>
    <Word Name="MODAXVAL" Type="function_call">
      <Function Name="SiemensMODAXVAL" Type="normal"/>
    </Word>
    <Word Name="MOVT" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="MU1" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond"/>
    </Word>
    <Word Name="N" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="8.0" MetricType="decimal" MetricFormat="8.0" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="NAMETOINT" Type="function_call">
      <Function Name="StringToArrayIndex" Type="normal"/>
    </Word>
    <Word Name="NEWCONF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="NORM" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="NOT" Type="function_call">
      <Function Name="NOT" Type="normal"/>
    </Word>
    <Word Name="NUMBER" Type="function_call">
      <Function Name="NUMBER" Type="normal"/>
    </Word>
    <Word Name="NUM_INPUT" Type="function_call">
      <Function Name="NumInput" Type="normal"/>
    </Word>
    <Word Name="OFFN" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="OPEN" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="OR" Type="or">
    </Word>
    <Word Name="ORIAXES" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ORICONCCW" Type="ignore">
    </Word>
    <Word Name="ORICONCW" Type="ignore">
    </Word>
    <Word Name="ORIEULER" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ORIMKS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ORIPLANE" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ORIROTA" Type="ignore">
    </Word>
    <Word Name="ORIROTT" Type="ignore">
    </Word>
    <Word Name="ORIRPY" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ORISOL" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ORISOLH" Type="function_call">
      <Function Name="ORISOLH2" Type="normal"/>
    </Word>
    <Word Name="ORIVECT" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ORIWKS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="OVR" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="P" Type="macro_call">
      <Value Type="composite_numeric" Format="* 4"/>
    </Word>
    <Word Name="PAROT" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="PAROTOF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="PCALL" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="PL" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="PLAY_SOUND" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="PM" Type="function_call">
      <Function Name="abs" Type="normal"/>
    </Word>
    <Word Name="POLY" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="POT" Type="function_call">
      <Function Name="sqr" Type="normal"/>
    </Word>
    <Word Name="PO[X]=" Type="macro_call">
      <Value Type="list_numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="PO[Y]=" Type="macro_call">
      <Value Type="list_numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="PO[Z]=" Type="macro_call">
      <Value Type="list_numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="PREPRO" Type="ignore">
    </Word>
    <Word Name="PROC" Type="macro_call">
      <Value Type="alpha_numeric_plus"/>
    </Word>
    <Word Name="PTP" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="PTPG0" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="PW" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="P_SUPPORT_C" Type="variable_name">
    </Word>
    <Word Name="Q" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="QU" Type="function_call">
      <Function Name="abs" Type="normal"/>
    </Word>
    <Word Name="R" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="Siemens840DRCond"/>
    </Word>
    <Word Name="RDISABLE" Type="begin_comment">
    </Word>
    <Word Name="READ" Type="sin840D_READ">
    </Word>
    <Word Name="REDEF" Type="begin_comment">
    </Word>
    <Word Name="RELEASE" Type="begin_comment">
    </Word>
    <Word Name="REP" Type="S840D_rep">
    </Word>
    <Word Name="REPEAT" Type="S840D_repeat">
    </Word>
    <Word Name="REPEATB" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="RET" Type="macro_call">
      <Value Type="list_alpha_numeric"/>
    </Word>
    <Word Name="RINDEX" Type="function_call">
      <Function Name="RINDEX" Type="normal"/>
    </Word>
    <Word Name="RND" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="RNDM" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="ROT" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="ROUND" Type="function_call">
      <Function Name="Round" Type="normal"/>
    </Word>
    <Word Name="ROUNDUP" Type="function_call">
      <Function Name="ceil" Type="normal"/>
    </Word>
    <Word Name="RP" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="RPL" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="RT" Type="var_name">
    </Word>
    <Word Name="RTOI" Type="function_call">
      <Function Name="IntTrunc" Type="normal"/>
    </Word>
    <Word Name="S" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="5.0" MetricType="decimal" MetricFormat="5.0" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensSpindleCond"/>
    </Word>
    <Word Name="SAVE" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="SBLOF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="SBLON" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="SC" Type="var_name">
    </Word>
    <Word Name="SCALE" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="SD" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="SET" Type="S840D_set">
    </Word>
    <Word Name="SETINT" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="SETM" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="SETMS" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="SF=" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="SIN" Type="function_call">
      <Function Name="sin_d" Type="normal"/>
    </Word>
    <Word Name="SK" Type="macro_call">
      <Value Type="list_numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="SOFT" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="SOFTA" Type="macro_call">
      <Value Type="list_alpha_numeric"/>
    </Word>
    <Word Name="SPCOF" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="SPCON" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="SPI" Type="function_call">
      <Function Name="SiemensSPI" Type="normal"/>
    </Word>
    <Word Name="SQRT" Type="function_call">
      <Function Name="sqrt" Type="normal"/>
    </Word>
    <Word Name="START" Type="macro_call">
      <Value Type="list_numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="STARTFIFO" Type="ignore">
    </Word>
    <Word Name="STOPRE" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="STRLEN" Type="function_call">
      <Function Name="STRLEN" Type="normal"/>
    </Word>
    <Word Name="ST_CUST" Type="ignore">
    </Word>
    <Word Name="SUBROUTINENAME" Type="macro_call">
      <Value Type="alpha_numeric_plus"/>
    </Word>
    <Word Name="SUBSTR" Type="function_call">
      <Function Name="SUBSTR" Type="normal"/>
    </Word>
    <Word Name="SUPA" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="T" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="TAN" Type="function_call">
      <Function Name="tan_d" Type="normal"/>
    </Word>
    <Word Name="TCOABS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TC_1" Type="variable_name">
    </Word>
    <Word Name="TC_2" Type="variable_name">
    </Word>
    <Word Name="TC_3" Type="variable_name">
    </Word>
    <Word Name="TC_4" Type="variable_name">
    </Word>
    <Word Name="TC_Y" Type="variable_name">
    </Word>
    <Word Name="TC_Z" Type="variable_name">
    </Word>
    <Word Name="TEXT_INPUT" Type="function_call">
      <Function Name="OperatorTextInput" Type="normal"/>
    </Word>
    <Word Name="TO" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensTOCondWord"/>
    </Word>
    <Word Name="TOFRAME" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOFRAMEX" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOFRAMEY" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOFRAMEZ" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOLOWER" Type="function_call">
      <Function Name="TOLOWER" Type="normal"/>
    </Word>
    <Word Name="TOOL_CHANGE" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond"/>
    </Word>
    <Word Name="TOROT" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOROTOF" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOROTX" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOROTY" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOROTZ" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOUPPER" Type="function_call">
      <Function Name="TOUPPER" Type="normal"/>
    </Word>
    <Word Name="TOWBCS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOWKCS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOWMCS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOWSTD" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOWTCS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TOWWCS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TR" Type="var_name">
    </Word>
    <Word Name="TRACYL" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="TRANS" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="TRANSMIT" Type="macro_call">
      <Value Type="list_numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="TRUNC" Type="function_call">
      <Function Name="IntTrunc" Type="normal"/>
    </Word>
    <Word Name="TURN" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="U" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="UNBLANK" Type="macro_call">
      <Value Type="alpha_numeric"/>
    </Word>
    <Word Name="UNTIL" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="UPATH" Type="ignore">
    </Word>
    <Word Name="USERENDPROG" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="USERPARATAB1" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="USERSTARTPROG" Type="macro_call">
      <Value Type="none"/>
    </Word>
    <Word Name="V" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="VALUE_INPUT" Type="function_call">
      <Function Name="OperatorValueInput" Type="normal"/>
    </Word>
    <Word Name="VELOLIMA" Type="macro_call">
      <Value Type="list_alpha_numeric"/>
    </Word>
    <Word Name="W" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="WAITC" Type="begin_comment">
    </Word>
    <Word Name="WAITM" Type="macro_call">
      <Value Type="list_numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="WAITMC" Type="begin_comment">
    </Word>
    <Word Name="WAITS" Type="begin_comment">
    </Word>
    <Word Name="WHEN" Type="macro_call">
      <Value Type="text_string"/>
    </Word>
    <Word Name="WHENEVER" Type="macro_call">
      <Value Type="text_string"/>
    </Word>
    <Word Name="WHENEVERS" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="WHENS" Type="macro_call">
      <Value Type="text_string"/>
    </Word>
    <Word Name="WHILE" Type="macro_call">
      <Value Type="numeric" InchType="decimal" InchFormat="" MetricType="decimal" MetricFormat="" Multiply="off" Multiplier="1"/>
    </Word>
    <Word Name="WRITE" Type="sin840D_WRITE">
    </Word>
    <Word Name="WRTPR" Type="begin_comment">
    </Word>
    <Word Name="X" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="XOR" Type="bitwise_xor">
    </Word>
    <Word Name="X_COLLET" Type="variable_name">
    </Word>
    <Word Name="Y" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="Y_COLLET" Type="variable_name">
    </Word>
    <Word Name="Z" Type="conditional">
      <Value Type="numeric" InchType="decimal" InchFormat="4.4" MetricType="decimal" MetricFormat="5.3" Multiply="off" Multiplier="1"/>
      <Function Name="SiemensAXISCond3"/>
    </Word>
    <Word Name="Z_COLLET" Type="variable_name">
    </Word>
  </Words>
  <NCSubstitutions>
    <Substitution Input="AP=IC" Output="INC_AP"/>
    <Substitution Input="$AA_SOFTENDP" Output="$MA_POS_LIMIT_PLUS"/>
    <Substitution Input="$AA_SOFTENDN" Output="$MA_POS_LIMIT_MINUS"/>
    <Substitution Input="BLG94 FB=_FC" Output="G94 F=_FC"/>
    <Substitution Input="STRINGIS($MC_AXCONF_CHANAX_NAME_TAB[_J])&lt;&gt;201" Output="0"/>
    <Substitution Input="ISVAR(&quot;$MCS_FUNCTION_MASK_TECH&quot;)" Output="($MCS_FUNCTION_MASK_TECH &lt;&gt; 0)"/>
    <Substitution Input="ISVAR(&quot;NAMETOINT&quot;)" Output="1"/>
    <Substitution Input="_ALARM=GETTCOR" Output="GETTCOR"/>
    <Substitution Input="_I=GETTCOR" Output="GETTCOR"/>
    <Substitution Input="_ERR=GETTCOR" Output="GETTCOR"/>
    <Substitution Input="/_N_MPF_DIR/" Output=" "/>
    <Substitution Input="/_N_CST_DIR/" Output=" "/>
    <Substitution Input="~&quot;" Output="||"/>
    <Substitution Input="G75 Z1=0." Output="G53 G0 Z410"/>
    <Substitution Input="G75 Y1=0 X1=0" Output="G53 G0 X-480 Y180"/>
  </NCSubstitutions>
  <OPSubstitutions>
  </OPSubstitutions>
  <SuperGroup Name="Specials">
    <Group Name=":" Type="word" Description="BRANCHING: Label" Field="0">
      <ConditionMacro Description="Combined with InverseWordValue in SOP">
        <Macro Name="LabelMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="%_N_" Type="word" Description="SUBROUTINES: Subroutine suffix" Field="0">
      <ConditionMacro Description="Enters in SAVE procedure">
        <Macro Name="Siemens840DSubroutineProc" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="BlockFinish" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="CurrentSubroutineName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#CurSubName}"/>
        </Variable>
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_PROG"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="%L" Type="word" Description="SUBROUTINES: Subroutine suffix" Field="0">
      <ConditionMacro Description="Enters in SAVE procedure">
        <Macro Name="SubroutineSequence" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_PROG"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="%MPF" Type="word" Description="SUBROUTINES: Subroutine suffix - Main program" Field="0">
      <ConditionMacro Description="Enters in SAVE procedure">
        <Macro Name="SubroutineSequence" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_PROG"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="%SPF" Type="word" Description="SUBROUTINES: Subroutine suffix - Sub-program" Field="0">
      <ConditionMacro Description="Enters in SAVE procedure">
        <Macro Name="SubroutineSequence" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_PROG"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="N" Type="word" Description="SUBROUTINES: Sequence number" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Sequence" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="LabelMacro" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="N{$}"/>
        </Macro>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <SuperGroup Name="Branch">
    <Group Name="BLOCK" Type="word" Description="BRANCHING: Indirect subprogram call with specification of the calling program part" Field="0">
      <ConditionMacro Description="Combined with &quot;CALL&quot; and &quot;TO&quot;">
        <Macro Name="BlockBeginLabel" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CALL" Type="word" Description="SUBROUTINES: Indirect subprogram call" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ELSE" Type="word" Description="BRANCHING: Conditional statement and branch ELSE " Field="0">
      <ConditionMacro Description="Combined with &quot;IF&quot; and &quot;ENDIF&quot;.  Execution when: &lt;condition&gt; == FALSE">
        <Macro Name="ElseBlock" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ENDFOR" Type="word" Description="BRANCHING: Count loop" Field="0">
      <ConditionMacro Description="Combined with &quot;FOR&quot; and &quot;TO&quot;. Marks the end of the loop and results in a return jump to the beginning of the loop, as long as the end value of the count has still not been reached">
        <Macro Name="ForEndLoop" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="END_VALUE"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ENDIF" Type="word" Description="BRANCHING: End IF block" Field="0">
      <ConditionMacro Description="Combined with &quot;IF&quot;. Marks the end of the conditional statement or branch">
        <Macro Name="EndIfBlockIgnore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ENDLOOP" Type="word" Description="BRANCHING: End DO Loop" Field="0">
      <ConditionMacro Description="Combined with &quot;LOOP&quot;. Marks the end of the loop and results in a return jump to the beginning of the loop">
        <Macro Name="EndLoop" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ENDWHILE" Type="word" Description="BRANCHING: End While Loop" Field="0">
      <ConditionMacro Description="Combined with &quot;WHILE&quot;. Marks the end of the loop and results in a return jump to the beginning of the loop">
        <Macro Name="EndLoop" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="-1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="FOR" Type="word" Description="BRANCHING: For loop" Field="0">
      <ConditionMacro Description="Combined with &quot;ENDFOR&quot;. Initiates the count loop">
        <Macro Name="ForLoop" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="GOTO" Type="word" Description="BRANCHING: Go To Sequence or Label" Field="0">
      <ConditionMacro Description="Jump operation first forward then backward">
        <Macro Name="Siemens840DGoto2" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="ConditionalEndOfBlock" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="GOTOB" Type="word" Description="BRANCHING: Go To Sequence or Label" Field="0">
      <ConditionMacro Description="Jump backward">
        <Macro Name="Siemens840DGoto2" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="-1"  Units="0"/>
        </Macro>
        <Macro Name="ConditionalEndOfBlock" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="GOTOC" Type="word" Description="BRANCHING: Go To Sequence or Label" Field="0">
      <ConditionMacro Description="As GOTO, but suppress alarm 14080 &quot;Jump destination not found&quot;">
        <Macro Name="Siemens840DGotoSuppress2" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="ConditionalEndOfBlock" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="GOTOF" Type="word" Description="BRANCHING: Go To Sequence or Label" Field="0">
      <ConditionMacro Description="Jump forward">
        <Macro Name="Siemens840DGoto2" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="ConditionalEndOfBlock" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="IF" Type="word" Description="BRANCHING: Introduction of a conditional jump" Field="0">
      <ConditionMacro Description="Combined with &quot;GOTO&quot; Forwards, i.e: If (expression) GOTO 30">
        <CondWord Logical="and" Name="GOTO"/>
        <Macro Name="IfCheckZero" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Combined with &quot;GOTOB&quot; Backwords, i.e: If (expression) GOTOB 30">
        <CondWord Logical="and" Name="GOTOB"/>
        <Macro Name="IfCheckZero" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Combined with &quot;GOTOC&quot; Forwards, i.e: If (expression) GOTOC 30">
        <CondWord Logical="and" Name="GOTOC"/>
        <Macro Name="IfCheckZero" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Combined with &quot;GOTOF&quot; Forwards, i.e: If (expression) GOTOF 30">
        <CondWord Logical="and" Name="GOTOF"/>
        <Macro Name="IfCheckZero" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Combined with &quot;ENDIF&quot;">
        <Macro Name="IfBlock" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="LOOP" Type="word" Description="BRANCHING: Introduction of an endless loop" Field="0">
      <ConditionMacro Description="Combined with &quot;ENDLOOP&quot;">
        <Macro Name="DoLoop" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PCALL" Type="word" Description="SUBROUTINES: Call subprograms with absolute path and parameter transfer" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TO" Type="word" Description="BRANCHING: Designates the end value in a FOR counter loop" Field="0">
      <ConditionMacro Description="Initiates the count loop - Counter loop with fixed number of passes">
        <CondWord Logical="and" Name="FOR"/>
        <Macro Name="ForToValue" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Together with the keyword &quot;TO&quot; defines the program part to be processed in an indirect subprogram call">
        <CondWord Logical="and" Name="BLOCK"/>
        <Macro Name="BlockEndLabel" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="UNTIL" Type="word" Description="BRANCHING: Condition for end of REPEAT loop" Field="0">
      <ConditionMacro Description="Combined with &quot;REPEAT&quot;">
        <Macro Name="UntilLoop" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="WHILE" Type="word" Description="BRANCHING: Start of WHILE program loop" Field="0">
      <ConditionMacro Description="Combined with &quot;ENDWHILE&quot;. Initiates the program loop">
        <Macro Name="WhileLoop" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="DoLoop" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <SuperGroup Name="States">
    <Group Name="BSPLINE" Type="word" Description="MOTION: Command to activate B spline interpolation" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="7"  Units="0"/>
        </Variable>
        <Macro Name="MotionNurbs" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="NurbsInitialControl" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DIAMON" Type="word" Description="MOTION: X-Axis Multiplier 0.5" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[29]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="XAxisMultiplier" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0.5"  Units="0"/>
        </Macro>
        <Macro Name="Siemens840DCallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_DIAMONOF"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DIAM90" Type="word" Description="MOTION: X-Axis Multiplier 0.5" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[29]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Macro Name="XAxisMultiplier" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0.5"  Units="0"/>
        </Macro>
        <Macro Name="Siemens840DCallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_DIAMONOF"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DIAMOF" Type="word" Description="MOTION: X-Axis Multiplier 1" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[29]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="XAxisMultiplier" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="Siemens840DCallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_DIAMONOF"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Linear interpolation with rapid traverse" Range="0" Field="0">
      <ConditionMacro Description="Combined with &quot;MCALL&quot;">
        <CondVariable Logical="and" Name="McallSubroutineOn" Range="1"/>
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="MotionRapid" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="XAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="MotionRapid" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Linear interpolation with feedrate" Range="1" Field="0">
      <ConditionMacro Description="Combined with &quot;MCALL&quot;">
        <CondVariable Logical="and" Name="McallSubroutineOn" Range="1"/>
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="MotionLinear" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="XAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="MotionLinear" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Circular/helical interpolation CW" Range="2" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Macro Name="MotionCW" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Circular/helical interpolation CCW" Range="3" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="4"  Units="0"/>
        </Variable>
        <Macro Name="MotionCCW" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Exact stop - Deceleration - Non-modal " Range="9" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Selection of working plane X/Y" Range="17" Field="0">
      <ConditionMacro Description="">
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN1;{#$MC_AXCONF_GEOAX_NAME_TAB[0]};G17"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN2;{#$MC_AXCONF_GEOAX_NAME_TAB[1]};G17"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN3;{#$MC_AXCONF_GEOAX_NAME_TAB[2]};G17"/>
        </Macro>
        <Variable Name="$P_GG[6]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="MotionPlaneXY" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Selection of working plane Z/X" Range="18" Field="0">
      <ConditionMacro Description="">
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN1;{#$MC_AXCONF_GEOAX_NAME_TAB[2]};G18"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN2;{#$MC_AXCONF_GEOAX_NAME_TAB[0]};G18"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN3;{#$MC_AXCONF_GEOAX_NAME_TAB[1]};G18"/>
        </Macro>
        <Variable Name="$P_GG[6]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="MotionPlaneZX" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Selection of working plane Y/Z" Range="19" Field="0">
      <ConditionMacro Description="">
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN1;{#$MC_AXCONF_GEOAX_NAME_TAB[1]};G19"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN2;{#$MC_AXCONF_GEOAX_NAME_TAB[2]};G19"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN3;{#$MC_AXCONF_GEOAX_NAME_TAB[0]};G19"/>
        </Macro>
        <Variable Name="$P_GG[6]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Macro Name="MotionPlaneYZ" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Lower working area limitation" Range="25" Field="0">
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Upper working area limitation" Range="26" Field="0">
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="TURNING CYCLES: Thread cutting with constant lead" Range="33" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="10"  Units="0"/>
        </Variable>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CycleTurnThread" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Suppression of current zero offset (non-modal)" Range="53" Field="0">
      <ConditionMacro Description="G53, G153 and SUPA cause block-by-block suppression of work offsets, active tool length offset and tool radius offset">
        <CondVariable Logical="and" Name="$MN_G53_TOOLCORR" Range="1"/>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
        <Macro Name="SiemensUpdateActframeSuppress" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="IFRAME TOOLFRAME WPFRAME PFRAME CYCFRAME"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="With bit 0 set the tool length is only suppressed with G53, G153 and SUPA, if a cutting edge is not selected in the same block (this can also be the cutting edge that is already active)">
        <CondVariable Logical="and" Name="$MN_G53_TOOLCORR" Range="3"/>
        <CondWord Logical="and_not" Name="D"/>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
        <Macro Name="SiemensUpdateActframeSuppress" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="IFRAME TOOLFRAME WPFRAME PFRAME CYCFRAME"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="G53, G153 and SUPA cause block-by-block suppression of work offsets. The active tool length offset and tool radius offset remain active">
        <Macro Name="SiemensUpdateActframeSuppress" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="IFRAME TOOLFRAME WPFRAME PFRAME CYCFRAME"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="WORK OFFSETS: Call the second to fifth settable zero offset/frame" Range="54-57" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[8]" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="$ - 52"  Units="0"/>
        </Variable>
        <Variable Name="$P_UIFRNUM" Description="Work Offset " Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="$ - 53"  Units="0"/>
        </Variable>
        <Macro Name="SiemensSetFrame2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_UIFR[{$-53}] $P_IFRAME"/>
        </Macro>
        <Macro Name="SiemensUpdateActBframe" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="COPY"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Exact stop - Deceleration - Modal " Range="60" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[10]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Corner deceleration at inside corners when tool radius offset is active (G41, G42)" Range="62" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Thread cutting with constant lead" Range="63" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="10"  Units="0"/>
        </Variable>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="MotionLinear" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Continuous-path mode" Range="64" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[10]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="UNITS: Inch dimensions for geometric specifications (lengths)" Range="70" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UnitsInch" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="UNITS: Metric dimensions for geometric specifications (lengths)" Range="71" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
        <Macro Name="UnitsMetric" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Absolute dimensions" Range="90" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[14]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ModeAbsolute" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Incremental dimensions" Range="91" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[14]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ModeIncremental" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="FEEDS &amp; SPEEDS: Spindle speed limitation with v constant" Range="92" Field="0">
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="FEEDS &amp; SPEEDS: Inverse-time feedrate RPM" Range="93" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="FeedModeTime" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="FEEDS &amp; SPEEDS: Linear feedrate F in mm/min or inch/min and degree/min" Range="94" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="FeedModeMinute" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="FEEDS &amp; SPEEDS: Revolutional feedrate F in mm/rev or inch/rev" Range="95" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="FEEDS &amp; SPEEDS: Revolutional feedrate (as for G95) and constant cutting rate" Range="96" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="4"  Units="0"/>
        </Variable>
        <Macro Name="ConstantSurfaceSpeedMode" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="SetMotionFlag" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="FEEDS &amp; SPEEDS: Revolutional feedrate and constant spindle speed (constant cutting rate OFF)" Range="97" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Macro Name="RPMMode" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="TANGENTIAL APPROACH AND EXIT: Soft approach with straight line" Range="147" Field="0">
      <ConditionMacro Description="">
        <Macro Name="TangentialInit" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TangentialMethod" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="TANGENTIAL APPROACH AND EXIT: Soft retraction with straight line" Range="148" Field="0">
      <ConditionMacro Description="">
        <Macro Name="TangentialInit" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="TangentialMethod" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Suppression of current frames including basic frame" Range="153" Field="0">
      <ConditionMacro Description="G53, G153 and SUPA cause block-by-block suppression of work offsets, active tool length offset and tool radius offset">
        <CondVariable Logical="and" Name="$MN_G53_TOOLCORR" Range="1"/>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
        <Macro Name="SiemensUpdateActframeSuppress" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="With bit 0 set the tool length is only suppressed with G53, G153 and SUPA, if a cutting edge is not selected in the same block (this can also be the cutting edge that is already active)">
        <CondVariable Logical="and" Name="$MN_G53_TOOLCORR" Range="3"/>
        <CondWord Logical="and_not" Name="D"/>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
        <Macro Name="SiemensUpdateActframeSuppress" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="G53, G153 and SUPA cause block-by-block suppression of work offsets. The active tool length offset and tool radius offset remain active">
        <Macro Name="SiemensUpdateActframeSuppress" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="TANGENTIAL APPROACH AND EXIT: Soft approach with quadrant" Range="247" Field="0">
      <ConditionMacro Description="">
        <Macro Name="TangentialInit" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TangentialMethod" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="TANGENTIAL APPROACH AND EXIT: Soft retraction with quadrant" Range="248" Field="0">
      <ConditionMacro Description="">
        <Macro Name="TangentialInit" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="TangentialMethod" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="DRILL CYCLES: Rigid tapping, positive lead, clockwise" Range="331" Field="0">
      <ConditionMacro Description="Direction of rotation after end of cycle CYCLE84">
        <CondVariable Logical="and" Name="PIT" Range="&lt; 0"/>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="MotionLinear" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="MotionLinear" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="DRILL CYCLES: Rigid tapping, negative lead, counter-clockwise" Range="332" Field="0">
      <ConditionMacro Description="Direction of rotation after end of cycle CYCLE84">
        <CondVariable Logical="and" Name="PIT" Range="&lt; 0"/>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="MotionLinear" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="MotionLinear" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Initial infeed on perpendicular axis (z), then approach in plane" Range="341" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="TANGENTIAL APPROACH AND EXIT : Soft approach with semicircle" Range="347" Field="0">
      <ConditionMacro Description="">
        <Macro Name="TangentialInit" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TangentialMethod" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="TANGENTIAL APPROACH AND EXIT: Soft retraction with semicircle" Range="348" Field="0">
      <ConditionMacro Description="">
        <Macro Name="TangentialInit" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="TangentialMethod" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="WORK OFFSETS: Call G500 or Call the 6th to the 99th settable zero offset" Range="500 505-599" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[8]" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="$ - 499"  Units="0"/>
        </Variable>
        <Variable Name="$P_UIFRNUM" Description="Work Offset " Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="$ - 500"  Units="0"/>
        </Variable>
        <Macro Name="SiemensSetFrame2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_UIFR[{$-500}] $P_IFRAME"/>
        </Macro>
        <Macro Name="SiemensUpdateActBframe" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="COPY"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Block change at exact stop fine" Range="601" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[12]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Block change at exact stop coarse" Range="602" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[12]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Block change at IPO block end" Range="603" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[12]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Corner deceleration at all corners" Range="621" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description=" ACCEL/DECEL: Continuous-path mode with smoothing as per distance criterion (= programmable rounding clearance)" Range="641" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[10]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Continuous-path mode with smoothing within the defined tolerances" Range="642" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[10]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Continuous-path mode with smoothing within the defined tolerances (block-internal)" Range="643" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[10]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description=" ACCEL/DECEL: Continuous-path mode with smoothing with maximum possible dynamic response" Range="644" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[10]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="ACCEL/DECEL: Continuous-path mode with smoothing and tangential block transitions within the defined tolerances" Range="645" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[10]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="UNITS: Inch dimensions for geometric and technological specifications (lengths, feedrate)" Range="700" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UnitsInch" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="UNITS: Metric dimensions for geometric and technological specifications (lengths, feedrate)" Range="710" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="4"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
        <Macro Name="UnitsMetric" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="FEEDS &amp; SPEEDS: Linear feedrate (as for G94) and constant cutting rate" Range="961" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="7"  Units="0"/>
        </Variable>
        <Macro Name="ConstantSurfaceSpeedMode" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="FeedModeMinute" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="FEEDS &amp; SPEEDS: Linear feedrate and constant spindle speed (constant cutting rate OFF)" Range="971" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="8"  Units="0"/>
        </Variable>
        <Macro Name="RPMMode" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="FeedModeMinute" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="INCH" Type="word" Description="UNITS: Inch dimensions for geometric and technological specifications (lengths, feedrate)" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="388"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="324"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="629792"/>
        </Variable>
        <Macro Name="UnitsInch" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="METRIC" Type="word" Description="UNITS: Metric dimensions for geometric and technological specifications (lengths, feedrate)" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="105216"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="384319120"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="705975"/>
        </Variable>
        <Macro Name="UnitsMetric" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SUPA" Type="word" Description="MOTION: Suppression of current zero offset, including programmed offsets, system frames, handwheel offsets (DRF), external zero offset, and overlaid movement" Field="0">
      <ConditionMacro Description="G53, G153 and SUPA cause block-by-block suppression of work offsets, active tool length offset and tool radius offset">
        <CondVariable Logical="and" Name="$MN_G53_TOOLCORR" Range="1"/>
        <Macro Name="SiemensUpdateActframeSuppress" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="With bit 0 set the tool length is only suppressed with G53, G153 and SUPA, if a cutting edge is not selected in the same block (this can also be the cutting edge that is already active)">
        <CondVariable Logical="and" Name="$MN_G53_TOOLCORR" Range="3"/>
        <CondWord Logical="and_not" Name="D"/>
        <Macro Name="SiemensUpdateActframeSuppress" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="G53, G153 and SUPA cause block-by-block suppression of work offsets. The active tool length offset and tool radius offset remain active">
        <Macro Name="SiemensUpdateActframeSuppress" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <SuperGroup Name="Indirect_States">
    <Group Name="CpDel" Type="variable" Description="Generic coupling: Deletion of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CpDel({$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[0]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(0, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[1]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(1, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[2]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(2, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[3]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(3, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[4]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(4, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[5]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(5, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[6]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(6, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[7]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(7, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[8]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(8, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[9]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(9, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[10]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(10, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[11]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(11, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[12]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(12, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[13]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(13, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[14]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(14, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[15]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(15, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[16]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(16, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[17]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(17, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[18]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(18, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[19]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(19, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[20]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(20, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[21]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(21, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[22]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(22, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[23]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(23, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[24]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(24, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[25]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(25, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[26]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(26, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[27]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(27, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[28]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(28, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[29]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(29, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CplDef[30]" Type="variable" Description="Generic coupling: Definition of a leading axis and creation of a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CplDef(30, {$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CpOf" Type="variable" Description="Generic coupling: Switching off a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CpOf({$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CpOn" Type="variable" Description="Generic coupling: Switching on a coupling module" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_CpOn({$$})"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[1]" Type="variable" Description="MOTION: Linear interpolation with rapid traverse - Indirect G0" Range="1" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="MotionRapid" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[1]" Type="variable" Description="MOTION: Linear interpolation with feedrate - Indirect G1" Range="2" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="MotionLinear" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[1]" Type="variable" Description="MOTION: Circular/helical interpolation CW - Indirect G2" Range="3" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="MotionCW" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[1]" Type="variable" Description="MOTION: Circular/helical interpolation CCW - Indirect G3" Range="4" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="MotionCCW" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[6]" Type="variable" Description="MOTION: Selection of working plane X/Y - Indirect G17" Range="1" Field="0">
      <ConditionMacro Description="">
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN1;{#$MC_AXCONF_GEOAX_NAME_TAB[0]};G17"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN2;{#$MC_AXCONF_GEOAX_NAME_TAB[1]};G17"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN3;{#$MC_AXCONF_GEOAX_NAME_TAB[2]};G17"/>
        </Macro>
        <Variable Name="$P_GG[6]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="MotionPlaneXY" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[6]" Type="variable" Description="MOTION: Selection of working plane Z/X - Indirect G18" Range="2" Field="0">
      <ConditionMacro Description="">
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN1;{#$MC_AXCONF_GEOAX_NAME_TAB[2]};G18"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN2;{#$MC_AXCONF_GEOAX_NAME_TAB[0]};G18"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN3;{#$MC_AXCONF_GEOAX_NAME_TAB[1]};G18"/>
        </Macro>
        <Variable Name="$P_GG[6]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="MotionPlaneZX" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[6]" Type="variable" Description="MOTION: Selection of working plane Y/Z - Indirect G19" Range="3" Field="0">
      <ConditionMacro Description="">
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN1;{#$MC_AXCONF_GEOAX_NAME_TAB[1]};G19"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN2;{#$MC_AXCONF_GEOAX_NAME_TAB[2]};G19"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_AXN3;{#$MC_AXCONF_GEOAX_NAME_TAB[0]};G19"/>
        </Macro>
        <Variable Name="$P_GG[6]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="MotionPlaneYZ" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[8]" Type="variable" Description="WORK OFFSETS: Call settable zero offset/frame - Indirect G54-57 G500-G599" Range="1-100" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[8]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_UIFRNUM" Description="Work Offset " Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="$ - 1"  Units="0"/>
        </Variable>
        <Macro Name="SiemensSetFrame2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_UIFR[{$-1}] $P_IFRAME"/>
        </Macro>
        <Macro Name="SiemensUpdateActBframe" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="COPY"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[13]" Type="variable" Description="UNITS: Inch dimensions for geometric specifications (lengths) - Indirect G70" Range="1" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UnitsInch" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[13]" Type="variable" Description="UNITS: Metric dimensions for geometric specifications (lengths) - Indirect G71" Range="2" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
        <Macro Name="UnitsMetric" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[13]" Type="variable" Description="UNITS: Inch dimensions for geometric and technological specifications (lengths, feedrate) - Indirect G700" Range="3" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UnitsInch" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[13]" Type="variable" Description="UNITS: Metric dimensions for geometric and technological specifications (lengths, feedrate) - Indirect G710" Range="4" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[13]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_METRIC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$MN_SCALING_SYSTEM_IS_INCH" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
        <Macro Name="UnitsMetric" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[14]" Type="variable" Description="MOTION: Absolute dimensions - Indirect G90" Range="1" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[14]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="ModeAbsolute" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[14]" Type="variable" Description="MOTION: Incremental dimensions - Indirect G91" Range="2" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[14]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="ModeIncremental" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[15]" Type="variable" Description="FEEDS &amp; SPEEDS: Inverse-time feedrate RPM - Indirect G93" Range="1" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="FeedModeTime" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[15]" Type="variable" Description="FEEDS &amp; SPEEDS: Linear feedrate F in mm/min or inch/min and degree/min - Indirect G94" Range="2" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="FeedModeMinute" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[15]" Type="variable" Description="FEEDS &amp; SPEEDS: Revolutional feedrate F in mm/rev or inch/rev - Indirect G95" Range="3" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[15]" Type="variable" Description="FEEDS &amp; SPEEDS: Revolutional feedrate (as for G95) and constant cutting rate- Indirect G96" Range="4" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="ConstantSurfaceSpeedMode" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[15]" Type="variable" Description="FEEDS &amp; SPEEDS: Revolutional feedrate and constant spindle speed (constant cutting rate OFF) - Indirect G97" Range="5" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[15]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="RPMMode" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="FeedModeRevolution" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[25]" Type="variable" Description="MOTION: Tool orientation reference" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[25]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="G[29]" Type="variable" Description="MOTION: Diameter programming: OFF - Indirect DIAMOF" Range="1" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[29]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="XAxisMultiplier" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[29]" Type="variable" Description="MOTION: Diameter programming: ON - Indirect DIAMON" Range="2" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[29]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="XAxisMultiplier" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0.5"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[29]" Type="variable" Description="MOTION: Diameter programming for G90, radius programming for G91 - Indirect DIAM90" Range="3" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[29]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Macro Name="XAxisMultiplier" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0.5"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CW" Range="3" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];{$}"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];1"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CCW" Range="4" Field="0">
      <ConditionMacro Description="">
        <Variable Name="CGT_SPINDLE" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];{$}"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];1"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn Off" Range="5" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];{$}"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];1"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="COOLANT: Coolant Mist" Range="7" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CoolantMist" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="COOLANT: Coolant On" Range="8" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantFlood" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="COOLANT: Coolant Off" Range="9" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Orient and Turn Off" Range="19" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];5"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];2"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Automatic gear change" Range="40" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 1" Range="41" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 2" Range="42" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 3" Range="43" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 4" Range="44" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 5" Range="45" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[0]" Type="variable" Description="" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CW" Range="3" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CCW" Range="4" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn Off" Range="5" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="COOLANT: Coolant Mist" Range="7" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CoolantMist" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="COOLANT: Coolant On" Range="8" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantFlood" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="COOLANT: Coolant Off" Range="9" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Orient and Turn Off" Range="19" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SDIR[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Automatic gear change" Range="40" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 1" Range="41" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 2" Range="42" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 3" Range="43" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 4" Range="44" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 5" Range="45" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[1]" Type="variable" Description="" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CW" Range="3" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="2"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[2]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[2]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CCW" Range="4" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="2"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[2]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[2]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn Off" Range="5" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="2"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[2]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[2]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="COOLANT: Coolant Mist" Range="7" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CoolantMist" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="COOLANT: Coolant On" Range="8" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantFlood" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="COOLANT: Coolant Off" Range="9" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Orient and Turn Off" Range="19" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="2"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SDIR[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Automatic gear change" Range="40" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 1" Range="41" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 2" Range="42" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 3" Range="43" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 4" Range="44" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 5" Range="45" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[2]" Type="variable" Description="" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CW" Range="3" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="3"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[3]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[3]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CCW" Range="4" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="3"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[3]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[3]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn Off" Range="5" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="3"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[3]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[3]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="COOLANT: Coolant Mist" Range="7" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CoolantMist" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="COOLANT: Coolant On" Range="8" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantFlood" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="COOLANT: Coolant Off" Range="9" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Orient and Turn Off" Range="19" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SDIR[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Automatic gear change" Range="40" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 1" Range="41" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 2" Range="42" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 3" Range="43" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 4" Range="44" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 5" Range="45" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[3]" Type="variable" Description="" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CW" Range="3" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="4"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[4]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CCW" Range="4" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="4"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[4]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[4]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn Off" Range="5" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="4"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[4]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[4]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="COOLANT: Coolant Mist" Range="7" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CoolantMist" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="COOLANT: Coolant On" Range="8" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantFlood" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="COOLANT: Coolant Off" Range="9" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Orient and Turn Off" Range="19" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="4"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SDIR[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Automatic gear change" Range="40" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 1" Range="41" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 2" Range="42" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 3" Range="43" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 4" Range="44" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 5" Range="45" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[4]" Type="variable" Description="" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CW" Range="3" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="5"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[5]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[5]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn On CCW" Range="4" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="5"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[5]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[5]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Turn Off" Range="5" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="5"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SDIR[5]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[5]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="COOLANT: Coolant Mist" Range="7" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CoolantMist" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="COOLANT: Coolant On" Range="8" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantFlood" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="COOLANT: Coolant Off" Range="9" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Orient and Turn Off" Range="19" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="5"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SDIR[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Automatic gear change" Range="40" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 1" Range="41" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 2" Range="42" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 3" Range="43" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 4" Range="44" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Gear step 5" Range="45" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M[5]" Type="variable" Description="" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="POS" Type="variable" Description="MOTION: Axis positioning" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensAXISMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="POSA" Type="variable" Description="MOTION: Position axis across block boundary" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensAXISMotion" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="WAIT"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SPOS[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="5"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[5]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="4"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[4]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="3"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[3]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="2"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[2]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOS[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOS[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="2"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOS[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="3"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOS[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="4"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOS[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="5"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOSA[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position across block boundaries" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="5"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[5]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="4"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[4]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="3"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[3]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="2"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[2]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOSA[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position across block boundaries" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOSA[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position across block boundaries" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="2"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[2]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOSA[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position across block boundaries" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="3"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[3]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOSA[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position across block boundaries" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="4"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[4]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SPOSA[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle position across block boundaries" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="5"/>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SPOS[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Variable Name="$P_SMODE[5]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="S[0]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Speed" Field="0">
      <ConditionMacro Description="Combined with G4 = Dwell Time">
        <CondWord Logical="and" Name="G" Range="4"/>
        <Macro Name="DwellTime" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="ActiveSpindleMinSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MIN_VELO_G25[$P_MSNUM];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MAX_VELO_G26[$P_MSNUM];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="92"/>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Orients corresponding Spindle">
        <CondWord Logical="and" Name="M" Range="19"/>
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Combined with &quot;MCALL&quot;">
        <CondWord Logical="and" Name="F"/>
        <CondState Logical="and" Name="MOTION_TYPE" Value="RAPID"/>
        <CondVariable Logical="and" Name="McallSubroutineOn" Range="1"/>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_S[{#$P_MSNUM}];{$}"/>
        </Macro>
        <Macro Name="XAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Combined with &quot;MCALL&quot;">
        <CondWord Logical="and" Name="F"/>
        <CondState Logical="and" Name="MOTION_TYPE" Value="LINEAR"/>
        <CondVariable Logical="and" Name="McallSubroutineOn" Range="1"/>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_S[{#$P_MSNUM}];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_S[{#$P_MSNUM}];{$}"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="S[1]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Speed" Field="0">
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMinSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MIN_VELO_G25[1];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MAX_VELO_G26[1];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="92"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="1"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[1]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[1]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="S[2]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Speed" Field="0">
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMinSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MIN_VELO_G25[2];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MAX_VELO_G26[2];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="92"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="2"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_S[2]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[2]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="S[3]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Speed" Field="0">
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMinSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MIN_VELO_G25[3];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MAX_VELO_G26[3];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="92"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="3"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_S[3]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[3]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="S[4]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Speed" Field="0">
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMinSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MIN_VELO_G25[4];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MAX_VELO_G26[4];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="92"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="4"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_S[4]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[4]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="S[5]" Type="variable" Description="FEEDS &amp; SPEEDS: Spindle Speed" Field="0">
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMinSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MIN_VELO_G25[5];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MAX_VELO_G26[5];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="92"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$P_MSNUM" Range="5"/>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$P_S[5]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleRestore" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[5]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="TCARR" Type="variable" Description="ACTIVATION: Request toolholder (number &quot;m&quot;)" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CallSubName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="TCARR"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$AN_TIMER[1]" Type="variable" Description="" Range="-1" Field="0">
      <ConditionMacro Description="">
        <Variable Name="CGT_TIME_SAVE" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$AC_TIME"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <SuperGroup Name="Cycles">
    <Group Name="G" Type="word" Description="DRILL CYCLES: Siemens Fixed Cycles - Pre-V2.6" Range="81-89" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CycleSubroutineOn" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="DRILL CYCLES: Siemens Fixed Cycles Cancel - Pre-V2.6" Range="80" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CycleSubroutineOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="MCALL" Type="word" Description="SUBROUTINES: Modal subprogram call" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CycleSubroutineOff" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="McallSubroutineOn" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
        <Variable Name="$P_MC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <SuperGroup Name="Registers">
    <Group Name="A" Type="word" Description="MOTION: A" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="AAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="AAxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="With TRAORI and ORIWKS">
        <CondVariable Logical="and_not" Name="$AC_TRAFO" Range="0"/>
        <CondVariable Logical="and" Name="$P_GG[25]" Range="1"/>
        <Macro Name="Ijk2AnglesInput" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#CGT_Default_Ijk2AnglesInput}"/>
        </Macro>
        <Macro Name="IjkAAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="AAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="A2" Type="word" Description="MOTION: A2" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="A2AxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="A2AxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="A2AxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="A3=" Type="word" Description="MOTION: Vector component designation" Field="0">
      <ConditionMacro Description="Use Ijk2AnglesLogic">
        <CondWord Logical="and" Name="B3="/>
        <CondWord Logical="and" Name="C3="/>
        <Macro Name="Ijk2AnglesInput" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="IJK"/>
        </Macro>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="IVector" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="MessageMacro" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="A3= B3= C3= must all be programmed"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="AN3=" Type="word" Description="MOTION: Vector component designation - Secondary Vector" Field="0">
      <ConditionMacro Description="Use Ijk2AnglesLogic">
        <CondWord Logical="and" Name="BN3="/>
        <CondWord Logical="and" Name="CN3="/>
        <CondWord Logical="and" Name="ORISOL"/>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="IJKVector2" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="MessageMacro" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="A3= B3= C3= must all be programmed"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ACCLIMA" Type="word" Description="ACCEL/DECEL: Effect of current maximum axial acceleration" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ADIS" Type="word" Description="ACCEL/DECEL: Rounding clearance for path functions G1, G2, G3, ..." Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ADISPOS" Type="word" Description="ACCEL/DECEL: Rounding clearance for rapid traverse G0" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ADISPOSA" Type="word" Description="ACCEL/DECEL: Size of the tolerance window for IPOBRKA" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="AP" Type="word" Description="MOTION: Polar angle" Field="0">
      <ConditionMacro Description="Pole programming relative to the last programmed setpoint position">
        <CondWord Logical="and" Name="G" Range="110-112"/>
        <Variable Name="$P_AP" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="Absolute Mode">
        <CondState Logical="and" Name="ABS_INC" Value="ABSOLUTE"/>
        <Variable Name="$P_AP" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="PolarCoordOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="PolarCoordAngle" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="PolarCoordOnOff" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Incremental Mode">
        <CondState Logical="and" Name="ABS_INC" Value="INCREMENTAL"/>
        <Variable Name="$P_AP" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_AP + $"  Units="0"/>
        </Variable>
        <Macro Name="PolarCoordOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="PolarCoordIncAngle" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="PolarCoordOnOff" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="AR" Type="word" Description="CIRCLES: Opening angle" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CircleARParameter" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="B" Type="word" Description="MOTION: B" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="BAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="BAxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="With TRAORI and ORIWKS">
        <CondVariable Logical="and_not" Name="$AC_TRAFO" Range="0"/>
        <CondVariable Logical="and" Name="$P_GG[25]" Range="1"/>
        <Macro Name="Ijk2AnglesInput" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#CGT_Default_Ijk2AnglesInput}"/>
        </Macro>
        <Macro Name="IjkBAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="BAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="B2" Type="word" Description="MOTION: B2" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="B2AxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="B2AxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="B2AxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="B3=" Type="word" Description="MOTION: Vector component designation" Field="0">
      <ConditionMacro Description="Use Ijk2AnglesLogic">
        <CondWord Logical="and" Name="A3="/>
        <CondWord Logical="and" Name="C3="/>
        <Macro Name="Ijk2AnglesInput" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="IJK"/>
        </Macro>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="JVector" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="MessageMacro" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="A3= B3= C3= must all be programmed"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="BN3=" Type="word" Description="MOTION: Vector component designation - Secondary Vector" Field="0">
      <ConditionMacro Description="Use Ijk2AnglesLogic">
        <CondWord Logical="and" Name="AN3="/>
        <CondWord Logical="and" Name="CN3="/>
        <CondWord Logical="and" Name="ORISOL"/>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="IJKVector2" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="MessageMacro" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="A3= B3= C3= must all be programmed"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="BRISK" Type="word" Description="ACCEL/DECEL: Fast non-smoothed path acceleration" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="BRISKA" Type="word" Description="ACCEL/DECEL: Switch on brisk path acceleration for the programmed axes" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="C" Type="word" Description="MOTION: C" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="CAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="CAxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="With TRAORI and ORIWKS">
        <CondVariable Logical="and_not" Name="$AC_TRAFO" Range="0"/>
        <CondVariable Logical="and" Name="$P_GG[25]" Range="1"/>
        <Macro Name="Ijk2AnglesInput" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#CGT_Default_Ijk2AnglesInput}"/>
        </Macro>
        <Macro Name="IjkCAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="CAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="C2" Type="word" Description="MOTION: C2" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="C2AxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="C2AxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="C2AxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="C3=" Type="word" Description="MOTION: Vector component designation" Field="0">
      <ConditionMacro Description="Use Ijk2AnglesLogic">
        <CondWord Logical="and" Name="A3="/>
        <CondWord Logical="and" Name="B3="/>
        <Macro Name="Ijk2AnglesInput" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="IJK"/>
        </Macro>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="KVector" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="MessageMacro" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="A3= B3= C3= must all be programmed"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CANCEL" Type="word" Description="SYNC ACTIONS: Cancel modal synchronized action" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionCancelList" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CN3=" Type="word" Description="MOTION: Vector component designation - Secondary Vector" Field="0">
      <ConditionMacro Description="Use Ijk2AnglesLogic">
        <CondWord Logical="and" Name="AN3="/>
        <CondWord Logical="and" Name="BN3="/>
        <CondWord Logical="and" Name="ORISOL"/>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="IJKVector2" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="MessageMacro" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="A3= B3= C3= must all be programmed"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CFC" Type="word" Description="FEEDS &amp; SPEEDS: Constant feedrate on contour" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CFTCP" Type="word" Description="" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CHANDATA" Type="word" Description="MULTI-CHANNELS: Set channel number for channel data access" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SetSubsystemIDScan" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{$}"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CHF" Type="word" Description="CHAMFER/ROUND: Chamfer - Value = length of chamfer" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CornerMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Macro>
        <Macro Name="CornerValue" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CornerMode" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CHR" Type="word" Description="CHAMFER/ROUND: Chamfer - Value = length of chamfer in direction of movement" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CornerMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="CornerValue" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CornerMode" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CIP" Type="word" Description="MOTION: Circular interpolation through intermediate point" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Macro Name="Motion3DCircle" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CLEARM" Type="word" Description="SYNC: Reset one/several markers for channel coordination" Field="1">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DSyncClearMarker" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CLEARM" Type="word" Description="SYNC: Reset one/several markers for channel coordination" Field="2">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DSyncClearMarker" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CLEARM" Type="word" Description="SYNC: Reset one/several markers for channel coordination" Field="3">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DSyncClearMarker" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CLEARM" Type="word" Description="SYNC: Reset one/several markers for channel coordination" Field="4">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DSyncClearMarker" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CLEARM()" Type="word" Description="SYNC: Reset one/several markers for channel coordination" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DSyncClearMarker" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="ALL"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CONTPRON" Type="word" Description="TURNING CYCLES: Activate reference preprocessing" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensCONTPRON" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CP" Type="word" Description="MOTION: Path motion" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CR=" Type="word" Description="CIRCLES: Circle radius" Field="0">
      <ConditionMacro Description="Autoset Motion Plane ">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <CondWord Logical="and" Name="X"/>
        <CondWord Logical="and" Name="Z"/>
        <CondWord Logical="and_not" Name="Y"/>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleMotionPlaneZX" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Autoset Motion Plane ">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <CondWord Logical="and" Name="X"/>
        <CondWord Logical="and" Name="Z"/>
        <CondWord Logical="and_not" Name="Y"/>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleMotionPlaneZX" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Autoset Motion Plane ">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <CondWord Logical="and" Name="Y"/>
        <CondWord Logical="and" Name="Z"/>
        <CondWord Logical="and_not" Name="X"/>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleMotionPlaneYZ" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Autoset Motion Plane ">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <CondWord Logical="and" Name="Y"/>
        <CondWord Logical="and" Name="Z"/>
        <CondWord Logical="and_not" Name="X"/>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleMotionPlaneYZ" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Autoset Motion Plane ">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <CondWord Logical="and" Name="X"/>
        <CondWord Logical="and" Name="Y"/>
        <CondWord Logical="and_not" Name="Z"/>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleMotionPlaneXY" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Autoset Motion Plane ">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <CondWord Logical="and" Name="X"/>
        <CondWord Logical="and" Name="Y"/>
        <CondWord Logical="and_not" Name="Z"/>
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleMotionPlaneXY" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CUT2D" Type="word" Description="CUTTER COMPENSATION: 2D Tool Radius Compensation" Field="0">
      <ConditionMacro Description="Default setting at beginning of program">
        <Macro Name="Cut3dcMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CUT2DF" Type="word" Description="CUTTER COMPENSATION: 2D Tool Radius Compensation relative to the current frame (inclined plane)" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Cut3dcMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CUT3DC" Type="word" Description="CUTTER COMPENSATION: 3D Tool Radius Compensation for circumferential milling" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Cut3dcMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CUT3DCC" Type="word" Description="CUTTER COMPENSATION: 3D Tool Radius Compensation for circumferential milling taking into account a limitation surface with 3D radius compensation Contour on the machining surface" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Cut3dcMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CUT3DCCD" Type="word" Description="CUTTER COMPENSATION: 3D Tool Radius Compensation for circumferential milling taking into account a limitation surface with differential tool on the tool center point path Infeed to the limitation surface" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Cut3dcMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CUT3DF" Type="word" Description="CUTTER COMPENSATION: 3D Tool Radius Compensation for face milling with change in orientation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Cut3dcMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CUT3DFF" Type="word" Description="CUTTER COMPENSATION: 3D Tool Radius Compensation for face milling with constant orientation. The tool orientation is the direction defined by G17 - G19 and, in some cases, rotated by a frame" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Cut3dcMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CUT3DFS" Type="word" Description=" CUTTER COMPENSATION: 3D Tool Radius Compensation for face milling with constant orientation. The tool orientation is defined by G17 - G19 and is not influenced by frames" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Cut3dcMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="D" Type="word" Description="TOOL OFFSETS: Tool offset number" Field="0">
      <ConditionMacro Description="Deferred D value assignment">
        <CondWord Logical="and" Name="G" Range="53,153"/>
        <CondVariable Logical="and" Name="$MN_G53_TOOLCORR" Range="1"/>
        <Variable Name="$P_TOOL" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="Siemens840DCallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_SET_D"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Deferred D value assignment">
        <CondWord Logical="and" Name="SUPA"/>
        <CondVariable Logical="and" Name="$MN_G53_TOOLCORR" Range="1"/>
        <Variable Name="$P_TOOL" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="Siemens840DCallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CGT_SET_D"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Apply Tool Offsets Before Real Motion - Rotary Offsets">
        <CondVariable Logical="and" Name="_TCI" Range="&gt; 0"/>
        <CondVariable Logical="and" Name="_MODE_809" Range="0"/>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$TC_DP5[#$P_TOOLNO, $]+#$TC_DP14[#$P_TOOLNO, $]"  Units="3"/>
          <Override  Type="text"  Value="X"/>
        </Macro>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$TC_DP4[#$P_TOOLNO, $]+#$TC_DP13[#$P_TOOLNO, $]"  Units="3"/>
          <Override  Type="text"  Value="Y"/>
        </Macro>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$TC_DP3[#$P_TOOLNO, $]+#$TC_DP12[#$P_TOOLNO, $]"  Units="3"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
        <Macro Name="ToolCutterComp" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="SiemensApplyToolOffsets" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}]"/>
        </Macro>
        <Variable Name="$P_TOOL" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$TC_MPP4[9998,1]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$TC_DP5[#$P_TOOLNO, $]+#$TC_DP14[#$P_TOOLNO, $]"  Units="3"/>
          <Override  Type="text"  Value="X"/>
        </Macro>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$TC_DP4[#$P_TOOLNO, $]+#$TC_DP13[#$P_TOOLNO, $]"  Units="3"/>
          <Override  Type="text"  Value="Y"/>
        </Macro>
        <Macro Name="GageOffsetDirect" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$TC_DP3[#$P_TOOLNO, $]+#$TC_DP12[#$P_TOOLNO, $]"  Units="3"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
        <Macro Name="ToolCutterComp" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="TurnOnOffGageOffset" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_TOOL" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="$TC_MPP4[9998,1]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="DISPLOF" Type="word" Description="DISPLAY: Suppress current block display" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DISCL" Type="word" Description="MOTION: Clearance between the end point of the fast infeed motion and the machining plane" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DISR" Type="word" Description="MOTION: Distance for repositioning" Field="0">
      <ConditionMacro Description="">
        <Macro Name="TangentialRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DITRB" Type="word" Description="MOTION: Smoothing Length for Threading" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DL=" Type="word" Description="TOOL OFFSETS: Select location-dependent additive tool offset (DL, total set-up offset)" Field="0">
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DO" Type="word" Description="SYNC ACTIONS: Keyword for synchronized action, triggers action when condition is fulfilled" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionDo" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DRIVE" Type="word" Description="ACCEL/DECEL: Velocity-dependent path acceleration" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DRIVEA" Type="word" Description="ACCEL/DECEL: Activate knee-shaped acceleration characteristic for the programmed axes" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="E" Type="word" Description=" ROTATE 2D: Setup offsets" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="RotationAngle" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="SiemensShiftAngleA" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="RotateOrigin" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="RotationAngle" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="SiemensShiftAngleB" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="RotateOrigin" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ENDPROC" Type="word" Description="SUBROUTINES: End line of program with start line PROC" Field="0">
      <ConditionMacro Description="Enters in SAVE procedure">
        <Macro Name="ReturnFromSub" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="Siemens840DGoto" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_PROG_RETURN"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="EVERY" Type="word" Description="SYNC ACTIONS: Execute synchronized action on transition of condition from FALSE to TRUE" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionEvery" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="EXECTAB" Type="word" Description="TURNING CYCLES: Execute an element from a motion table" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensEXECTAB" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="EXTCALL" Type="word" Description="SUBROUTINES: Execute external subprogram" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DCallSubName" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="EXECUTE" Type="word" Description="COMPUTING: Program execution ON" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensEXECUTE" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="F" Type="word" Description="FEEDS &amp; SPEEDS" Field="0">
      <ConditionMacro Description="Dwell Time">
        <CondWord Logical="and" Name="G" Range="4"/>
        <Macro Name="DwellTime" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate Value">
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_F" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="FB" Type="word" Description="FEEDS &amp; SPEEDS: Non-modal feedrate" Field="0">
      <ConditionMacro Description="">
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_F" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="FAD" Type="word" Description="FEEDS &amp; SPEEDS: Infeed rate for soft approach and retraction" Field="0">
      <ConditionMacro Description="">
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_F" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="FFWOF" Type="word" Description="FEEDS &amp; SPEEDS : Feedforward control OFF" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="FFWON" Type="word" Description="FEEDS &amp; SPEEDS: Feedforward control ON" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="FLIN" Type="word" Description="FEEDS &amp; SPEEDS: Feed linear variable" Field="0">
      <ConditionMacro Description="">
        <Macro Name="FeedChangeMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="FNORM" Type="word" Description="FEEDS &amp; SPEEDS: Feedrate normal to DIN 66025" Field="0">
      <ConditionMacro Description="">
        <Macro Name="FeedChangeMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="FRC" Type="word" Description="FEEDS &amp; SPEEDS: Feedrate for radius and chamfer" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="FRCM" Type="word" Description="FEEDS &amp; SPEEDS: Feedrate for radius and chamfer, modal" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="FROM" Type="word" Description="SYNC ACTIONS: The action is executed if the condition is fulfilled once and as long as the synchronized action is active" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionFrom" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="H" Type="word" Description="PLC: Auxiliary function output to the PLC" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="I" Type="word" Description="CIRCLES: Interpolation parameters" Field="0">
      <ConditionMacro Description="Autoset Motion Plane + Circle center X">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <CondWord Logical="and" Name="X"/>
        <CondWord Logical="and" Name="Z"/>
        <CondWord Logical="and_not" Name="Y"/>
        <Macro Name="CircleMotionPlaneZX" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleCenterX" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Autoset Motion Plane + Circle center X">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <CondWord Logical="and" Name="X"/>
        <CondWord Logical="and" Name="Z"/>
        <CondWord Logical="and_not" Name="Y"/>
        <Macro Name="CircleMotionPlaneZX" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleCenterX" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Circle center X">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <Macro Name="CircleMotionPlaneXY" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleCenterX" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Circle center X">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <Macro Name="CircleMotionPlaneXY" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleCenterX" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate for threading">
        <CondWord Logical="and" Name="G" Range="33"/>
        <Macro Name="CycleTurnThreadLead" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate for threading">
        <CondWord Logical="and" Name="G" Range="331"/>
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate for threading">
        <CondWord Logical="and" Name="G" Range="332"/>
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ID" Type="word" Description="SYNC ACTIONS: Identifier for modal synchronized actions" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionID" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="IDS" Type="word" Description="SYNC ACTIONS: Identifier for modal static synchronized actions" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionID" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="I1=" Type="word" Description="CIRCLES: Intermediate point coordinate" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CircleIntermediatePoint" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="X"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="INC_AP" Type="word" Description="MOTION: Polar Coordinates (non-Modal) Incremental Polar Angle" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_AP" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_AP + $"  Units="0"/>
        </Variable>
        <Macro Name="PolarCoordOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="PolarCoordIncAngle" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="PolarCoordOnOff" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="INIT" Type="word" Description="SYNC: Selection of a particular NC program for execution in a particular channel" Field="1">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DSyncInit" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="INIT" Type="word" Description="SYNC: Selection of a particular NC program for execution in a particular channel" Field="2">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="INIT" Type="word" Description="SYNC: Selection of a particular NC program for execution in a particular channel" Field="3">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="INVCCW" Type="word" Description="MOTION: Trace involute, counter-clockwise" Field="0">
      <ConditionMacro Description="">
        <Macro Name="MotionCCWInvolute" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="INVCW" Type="word" Description="MOTION: Trace involute, clockwise" Field="0">
      <ConditionMacro Description="">
        <Macro Name="MotionCWInvolute" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="J" Type="word" Description="CIRCLES: Interpolation parameters" Field="0">
      <ConditionMacro Description="Autoset Motion Plane + Circle center Y">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <CondWord Logical="and" Name="Y"/>
        <CondWord Logical="and" Name="Z"/>
        <CondWord Logical="and_not" Name="X"/>
        <Macro Name="CircleMotionPlaneYZ" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleCenterY" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Autoset Motion Plane + Circle center Y">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <CondWord Logical="and" Name="Y"/>
        <CondWord Logical="and" Name="Z"/>
        <CondWord Logical="and_not" Name="X"/>
        <Macro Name="CircleMotionPlaneYZ" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleCenterY" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Circle center Y">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <Macro Name="CircleMotionPlaneXY" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleCenterY" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Circle center Y">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <Macro Name="CircleMotionPlaneXY" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CircleCenterY" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate for threading">
        <CondWord Logical="and" Name="G" Range="33"/>
        <Macro Name="CycleTurnThreadLead" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate for threading">
        <CondWord Logical="and" Name="G" Range="331"/>
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate for threading">
        <CondWord Logical="and" Name="G" Range="332"/>
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="J1=" Type="word" Description="CIRCLES: Intermediate point coordinate" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CircleIntermediatePoint" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="Y"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="JERKA" Type="word" Description="ACCEL/DECEL: Activate acceleration response set via MD for programmed axes" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="JERKLIM" Type="word" Description="ACCEL/DECEL: Reduction or overshoot of maximum axial jerk" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="JERKLIMA" Type="word" Description="ACCEL/DECEL: Reduction or overshoot of maximum axial jerk" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="K" Type="word" Description="CIRCLES: Interpolation parameters" Field="0">
      <ConditionMacro Description="Circle center Z">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <Macro Name="CircleCenterZ" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Circle center Z">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <Macro Name="CircleCenterZ" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate for threading">
        <CondWord Logical="and" Name="G" Range="33"/>
        <Macro Name="CycleTurnThreadLead" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="ABS($)"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate for threading">
        <CondWord Logical="and" Name="G" Range="331"/>
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="ABS($)"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Feedrate for threading">
        <CondWord Logical="and" Name="G" Range="332"/>
        <Macro Name="FeedRate" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="ABS($)"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="K1=" Type="word" Description="CIRCLES: Intermediate point coordinate" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CircleIntermediatePoint" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="Z"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="LIMS" Type="word" Description="FEEDS &amp; SPEEDS: Speed limitation for G96/G961 and G97" Field="0">
      <ConditionMacro Description="">
        <Macro Name="MaxTableRPM" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="MEAS" Type="word" Description="PROBING: Measurement with deletion of distance-to-go" Field="0">
      <ConditionMacro Description="Update System Variable $AA_MW">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <Variable Name="$MEAS" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="CallSubName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="UpdateProbingSystemVars"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Update System Variable $AA_MW">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <Variable Name="$MEAS" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="CallSubName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="UpdateProbingSystemVars"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Update System Variable $AA_MW">
        <Macro Name="Probe" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="RETURN= PROBE_HIT PROBE_X PROBE_Y PROBE_Z"/>
        </Macro>
        <Variable Name="$MEAS" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="CallSubName" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="UpdateProbingSystemVars"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="MOVT" Type="word" Description="MOTION: Specify end point of a traversing motion in the tool direction" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ToolAxisMotionXYZ" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="NORM" Type="word" Description="CUTTER COMPENSATION: Standard setting in starting point and end point with tool offset" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CutterCompValueDirect" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_TOOLR"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="OFFN" Type="word" Description=" CUTTER COMPENSATION: Allowance on the programmed contour" Field="0">
      <ConditionMacro Description="">
        <CondWord Logical="and" Name="G" Range="40"/>
        <Macro Name="CutterCompValueDirect" Scan="no" AfterMotion="yes">
          <Override  Type="expression"  Value="$ - #$P_OFFN + #CurCDC"  Units="0"/>
        </Macro>
        <Variable Name="$P_OFFN" Description="Additional CDC" Scan="no" AfterMotion="yes">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="CutterCompValueDirect" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="$ - #$P_OFFN + #CurCDC"  Units="0"/>
        </Macro>
        <Variable Name="$P_OFFN" Description="Additional CDC" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="ORIAXES" Type="word" Description="MOTION: Linear interpolation of machine axes or orientation axes" Field="0">
      <ConditionMacro Description="">
        <Macro Name="OriMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ORIEULER" Type="word" Description="MOTION: Orientation angle via Euler angle" Field="0">
      <ConditionMacro Description="">
        <Macro Name="RPY2Ijk" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ORIMKS" Type="word" Description="MOTION: Tool orientation in the machine coordinate system" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[25]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="ORIPLANE" Type="word" Description="MOTION: Interpolation in a plane (corresponds to ORIVECT), large-radius circular interpolation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="OriMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ORIRPY" Type="word" Description="MOTION: Orientation angle via RPY angle (XYZ)" Field="0">
      <ConditionMacro Description="">
        <Macro Name="RPY2Ijk" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ORIVECT" Type="word" Description="MOTION: Large-circle interpolation (identical to ORIPLANE)" Field="0">
      <ConditionMacro Description="">
        <Macro Name="OriMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ORIWKS" Type="word" Description="MOTION: Tool orientation in the workpiece coordinate system" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[25]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="OVR" Type="word" Description="FEEDS &amp; SPEEDS: Speed offset" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="P" Type="word" Description="BRANCHING: Number of subprogram repetitions" Field="0">
      <ConditionMacro Description="">
        <Macro Name="RepeatLoopCount" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PAROT" Type="word" Description="TOOL OFFSETS: Align workpiece coordinate system on workpiece" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensPAROT2" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}] SIEMENS_ROT_ORDER"/>
        </Macro>
        <Macro Name="AdjustToolOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="RpcpMatrixType" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="RefreshToolOffset" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[52]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="PAROTOF" Type="word" Description="TOOL OFFSETS: Deactivate frame rotation in relation to workpiece" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensPAROT2" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_GG[52]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="PL" Type="word" Description="NURBS POLY" Field="0">
      <ConditionMacro Description="Node clearance">
        <CondWord Logical="and" Name="BSPLINE"/>
        <Macro Name="SiemensNurbsKnot" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Node clearance">
        <CondState Logical="and" Name="MOTION_TYPE" Value="NURBS"/>
        <Macro Name="SiemensNurbsKnot" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Polynomial interpolation Length of the parameter interval for polynomial interpolation">
        <CondWord Logical="and" Name="POLY"/>
        <Macro Name="SiemensPolyT" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Polynomial interpolation Length of the parameter interval for polynomial interpolation">
        <CondState Logical="and" Name="MOTION_TYPE" Value="POLY"/>
        <Macro Name="SiemensPolyT" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="POLY" Type="word" Description="MOTION: Polynomial interpolation" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[1]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="9"  Units="0"/>
        </Variable>
        <Macro Name="MotionPoly" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PO[X]=" Type="word" Description=" NURBS POLY: Polynomial coefficient for polynomial interpolation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensPolyx" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PO[Y]=" Type="word" Description=" NURBS POLY: Polynomial coefficient for polynomial interpolation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensPolyy" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PO[Z]=" Type="word" Description=" NURBS POLY: Polynomial coefficient for polynomial interpolation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensPolyz" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PROC" Type="word" Description="SUBROUTINES: First operation in a program" Field="0">
      <ConditionMacro Description="Enters in SAVE procedure">
        <Variable Name="CurrentSubroutineName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#CurSubName}"/>
        </Variable>
        <Macro Name="Siemens840DProc" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_PROG"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PTP" Type="word" Description="MOTION: Point-to-point motion (PTP travel)" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PTPG0" Type="word" Description="MOTION: Point-to-point motion only with G0, otherwise path motion CP" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PW" Type="word" Description="NURBS POLY: B spline, point weight" Field="0">
      <ConditionMacro Description="">
        <Macro Name="NurbsWeight" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="Q" Type="word" Description="CIRCLES: Circle Radius" Field="0">
      <ConditionMacro Description="">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CW"/>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondState Logical="and" Name="MOTION_TYPE" Value="CCW"/>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="REPEATB" Type="word" Description="BRANCHING: Repetition of a program line" Field="0">
      <ConditionMacro Description="">
        <Macro Name="BlockBeginLabel" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="BlockEndLabel" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="RET" Type="word" Description="SUBROUTINES: End of subprogram" Range="NONE" Field="0">
      <ConditionMacro Description="Enters in SAVE procedure">
        <Macro Name="ReturnFromSub" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_PROG_RETURN"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="RET" Type="word" Description="SUBROUTINES: End of subprogram + Branching to Sequence" Field="0">
      <ConditionMacro Description="Enters in SAVE procedure">
        <Macro Name="ReturnFromSub" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="Siemens840DGoto" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_PROG_RETURN"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="RND" Type="word" Description="CHAMFER/ROUND: Round the contour corner" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CornerMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="CornerValue" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CornerMode" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="RNDM" Type="word" Description="CHAMFER/ROUND: Modal rounding" Field="0">
      <ConditionMacro Description="">
        <CondWord Logical="and" Name="RNDM" Range="0"/>
        <Macro Name="CornerMode" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="CornerMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="CornerValue" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="RP" Type="word" Description="MOTION: Polar radius" Field="0">
      <ConditionMacro Description="Pole programming relative to the last programmed setpoint position">
        <CondWord Logical="and" Name="G" Range="110-112"/>
        <Variable Name="$P_RP" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Variable Name="$P_RP" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="CircleRadius" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="PolarCoordOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="PolarCoordRadius" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="PolarCoordOnOff" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="RPL" Type="word" Description="ROTATION PLANE: Rotation in the plane" Field="0">
      <ConditionMacro Description="">
        <CondWord Logical="and" Name="ROT"/>
        <Macro Name="SiemensRPL" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <CondWord Logical="and" Name="AROT"/>
        <Macro Name="SiemensRPL" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="MessageMacro" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
          <Override  Type="text"  Value="Alarm 12110:  Syntax cannot be interpreted, need additional ROT or AROT"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SBLOF" Type="word" Description="DISPLAY: Suppress single block" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SBLON" Type="word" Description="DISPLAY: Revoke suppression of single block" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="S" Type="word" Description="FEEDS &amp; SPEEDS" Field="0">
      <ConditionMacro Description="Dwell Time">
        <CondWord Logical="and" Name="G" Range="4"/>
        <Macro Name="DwellTime" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="ActiveSpindleMinSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MAX_VELO_G26[{#$P_MSNUM}];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="ActiveSpindleMaxSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$SA_SPIND_MAX_VELO_G26[$P_MSNUM];{$}"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Spindle Orient">
        <CondWord Logical="and" Name="M" Range="19"/>
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Combined with CALL">
        <CondWord Logical="and" Name="F"/>
        <CondState Logical="and" Name="MOTION_TYPE" Value="RAPID"/>
        <CondVariable Logical="and" Name="McallSubroutineOn" Range="1"/>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="RPMSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="XAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Combined with CALL">
        <CondWord Logical="and" Name="F"/>
        <CondState Logical="and" Name="MOTION_TYPE" Value="LINEAR"/>
        <CondVariable Logical="and" Name="McallSubroutineOn" Range="1"/>
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="RPMSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="Spindle Speed">
        <Macro Name="ConstantSurfaceSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="ActiveSpindleSpeed" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_S[0]" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_S[{#$P_MSNUM}];{$}"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SAVE" Type="word" Description="SUBROUTINES: Attribute for saving information when subprograms are called" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_SAVE"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SD" Type="word" Description="NURBS POLY: Spline degree" Field="0">
      <ConditionMacro Description="">
        <Macro Name="NurbsDegree" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SETM" Type="word" Description="SYNC: Setting of markers in dedicated channel" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DSyncSetMarker" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SETMS" Type="word" Description="FEEDS &amp; SPEEDS: Reset to the master spindle defined in machine data" Range="1" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SpindleCompName[0];{#SpindleCompName[1]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SPOS[0];#SPOS[1]"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[0];#$P_SMODE[1]"/>
        </Macro>
        <Variable Name="$P_MSNUM" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="Active_Spindle" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SETMS" Type="word" Description="FEEDS &amp; SPEEDS: Reset to the master spindle defined in machine data" Range="2" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SpindleCompName[0];{#SpindleCompName[2]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SPOS[0];#SPOS[2]"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[0];#$P_SMODE[2]"/>
        </Macro>
        <Variable Name="$P_MSNUM" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="Active_Spindle" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SETMS" Type="word" Description="FEEDS &amp; SPEEDS: Reset to the master spindle defined in machine data" Range="3" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SpindleCompName[0];{#SpindleCompName[3]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SPOS[0];#SPOS[3]"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[0];#$P_SMODE[3]"/>
        </Macro>
        <Variable Name="$P_MSNUM" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="Active_Spindle" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SETMS" Type="word" Description="FEEDS &amp; SPEEDS: Reset to the master spindle defined in machine data" Range="4" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SpindleCompName[0];{#SpindleCompName[4]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SPOS[0];#SPOS[4]"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[0];#$P_SMODE[4]"/>
        </Macro>
        <Variable Name="$P_MSNUM" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="Active_Spindle" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SETMS" Type="word" Description="FEEDS &amp; SPEEDS: Reset to the master spindle defined in machine data" Range="5" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SpindleCompName[0];{#SpindleCompName[5]}"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SPOS[0];#SPOS[5]"/>
        </Macro>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[0];#$P_SMODE[5]"/>
        </Macro>
        <Variable Name="$P_MSNUM" Scan="no" AfterMotion="no">
        </Variable>
        <Variable Name="Active_Spindle" Scan="no" AfterMotion="no">
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="SF=" Type="word" Description="TURNING CYCLES: Starting point offset for thread cutting" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensCycle97ThreadStart" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SOFT" Type="word" Description="ACCEL/DECEL: Soft path acceleration" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SOFTA" Type="word" Description="ACCEL/DECEL: Activate jerk-limited axis acceleration for the programmed axes" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SPCOF" Type="word" Description="FEEDS &amp; SPEEDS: Switch master spindle or spindle(s) from position control to speed control" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SPCON" Type="word" Description="FEEDS &amp; SPEEDS: Switch master spindle or spindle(s) from speed control to position control" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="START" Type="word" Description="SYNC: Start selected programs simultaneously in several channels from current program" Range="1" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DSyncStart" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="START" Type="word" Description="SYNC: Start selected programs simultaneously in several channels from current program" Range="2" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="STOPRE" Type="word" Description="COMPUTING: Preprocessing stop until all prepared blocks in the main run are executed" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SUBROUTINENAME" Type="word" Description="SUBROUTINES: CGTech PROC" Field="0">
      <ConditionMacro Description="Combined with MCALL">
        <CondWord Logical="and" Name="MCALL"/>
        <Macro Name="McallSubroutineOn" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="yes">
        </Macro>
        <Variable Name="McallSubroutineOn" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Variable Name="$P_MC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="Siemens840DProcCall" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="T" Type="word" Description="TOOLING: Call tool (only change if specified in machine data; otherwise M6 command necessary) - Integer Ids" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensToolCode" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="SelectedTool" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{$$}"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="TCOABS" Type="word" Description="TOOL OFFSETS: Determine tool length components from the current tool orientation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="RefreshToolOffset" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_TCANG[3]" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_TCANG[1]"  Units="0"/>
        </Variable>
        <Variable Name="$P_TCANG[4]" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_TCANG[2]"  Units="0"/>
        </Variable>
        <Variable Name="$P_TCSOL" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="TOFRAME" Type="word" Description="ROTATION PLANE: Align Z axis of the WCS by rotating the frame parallel to the tool orientation + Translation to Tool Tip" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="_TCI" Range="&gt; 0"/>
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOFRAME3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}] Z"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOFRAME3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TOFRAMEX" Type="word" Description="ROTATION PLANE: Align Z axis of the WCS by rotating the frame parallel to the tool orientation + Translation to Tool Tip" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="_TCI" Range="&gt; 0"/>
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOFRAME3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}] X"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOFRAME3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="X"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TOFRAMEY" Type="word" Description="ROTATION PLANE: Align Z axis of the WCS by rotating the frame parallel to the tool orientation + Translation to Tool Tip" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="_TCI" Range="&gt; 0"/>
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOFRAME3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}] Y"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOFRAME3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="Y"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TOFRAMEZ" Type="word" Description="ROTATION PLANE: Align Z axis of the WCS by rotating the frame parallel to the tool orientation + Translation to Tool Tip" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="_TCI" Range="&gt; 0"/>
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOFRAME3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}] Z"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOFRAME3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TOROT" Type="word" Description="ROTATION PLANE: Align Z axis of the WCS by rotating the frame parallel to the tool orientation" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="_TCI" Range="&gt; 0"/>
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOROT3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}] Z"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOROT3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TOROTX" Type="word" Description="ROTATION PLANE: Align X axis of the WCS by rotating the frame parallel to the tool orientation" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="_TCI" Range="&gt; 0"/>
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOROT3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}] X"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOROT3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="X"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TOROTY" Type="word" Description="ROTATION PLANE: Align ZYaxis of the WCS by rotating the frame parallel to the tool orientation" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="_TCI" Range="&gt; 0"/>
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOROT3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}] Y"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOROT3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="Y"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TOROTZ" Type="word" Description="ROTATION PLANE: Align Z axis of the WCS by rotating the frame parallel to the tool orientation" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="_TCI" Range="&gt; 0"/>
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOROT3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="$TC_CARR13[{#TCARR}] $TC_CARR14[{#TCARR}] Z"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SiemensRotaryAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR35[{#TCARR}] $TC_CARR36[{#TCARR}]"/>
        </Macro>
        <Macro Name="SiemensTOROT3" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$SC_TOFRAME_MODE"  Units="0"/>
          <Override  Type="text"  Value="Z"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TOROTOF" Type="word" Description="ROTATION PLANE: Frame rotations in tool direction OFF" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensTOROTOF" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TRACYL" Type="word" Description="CYLINDRICAL/POLAR: Cylinder: Peripheral surface transformation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="RotaryControlPointOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="CGT_CYL_DIA" Scan="no" AfterMotion="no">
        </Variable>
        <Macro Name="CylindricalDiameter" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CylindricalInterpolation" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TRANSMIT" Type="word" Description="CYLINDRICAL/POLAR: Pole transformation (face machining)" Range="0" Field="0">
      <ConditionMacro Description="">
        <Macro Name="PolarInterpolation" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TRANSMIT" Type="word" Description="CYLINDRICAL/POLAR: Pole transformation (face machining)" Range="1" Field="0">
      <ConditionMacro Description="">
        <Macro Name="PolarInterpolation" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TRANSMIT" Type="word" Description="CYLINDRICAL/POLAR: Pole transformation (face machining)" Range="2" Field="0">
      <ConditionMacro Description="">
        <Macro Name="PolarInterpolation" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TURN" Type="word" Description="CIRCLES: Number of turns for helix" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="HelicalAddFullLoops" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="HelicalFullLoops" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="U" Type="word" Description="MOTION: U" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="UAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="UAxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="AROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="ASCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="ROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="SCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Tool 3D Offset X">
        <CondState Logical="and_not" Name="CUTTER_COMP" Value="OFF"/>
        <Macro Name="Tool3dXOffset" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="UAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="V" Type="word" Description="MOTION: V" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="VAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="VAxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="AROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="ASCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="ROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="SCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Tool 3D Offset Y">
        <CondState Logical="and_not" Name="CUTTER_COMP" Value="OFF"/>
        <Macro Name="Tool3dYOffset" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="VAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="VELOLIMA" Type="word" Description="ACCEL/DECEL: Reduction or increase of the maximum axial velocity of the following axis" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="W" Type="word" Description="MOTION: W" Field="0">
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="WAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="WAxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="AROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="ASCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="ROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="SCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Tool 3D Offset Z">
        <CondState Logical="and_not" Name="CUTTER_COMP" Value="OFF"/>
        <Macro Name="Tool3dZOffset" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="WAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="WAITM" Type="word" Description="SYNC: Wait for marker in specified channel; terminate previous block with exact stop" Field="1">
      <ConditionMacro Description="">
        <Macro Name="Siemens840DSyncWaitMarker" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="WAITM" Type="word" Description="SYNC: Wait for marker in specified channel; terminate previous block with exact stop" Field="2">
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="WAITM" Type="word" Description="SYNC: Wait for marker in specified channel; terminate previous block with exact stop" Field="3">
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="WAITM" Type="word" Description="SYNC: Wait for marker in specified channel; terminate previous block with exact stop" Field="4">
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="WHEN" Type="word" Description="SYNC ACTIONS: The action is executed once whenever the condition is fulfilled" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionWhen" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="WHENS" Type="word" Description="SYNC ACTIONS: The action is executed once whenever the condition is fulfilled" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionWhen" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="WHENEVER" Type="word" Description="SYNC ACTIONS: The action is executed cyclically in each interpolator cycle when the condition is fulfilled" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionWhenever" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="WHENEVERS" Type="word" Description="SYNC ACTIONS: The action is executed cyclically in each interpolator cycle when the condition is fulfilled" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConditionalActionWhenever" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="X" Type="word" Description="MOTION: X" Field="0">
      <ConditionMacro Description="Dwell Time">
        <CondWord Logical="and" Name="G" Range="4"/>
        <Macro Name="DwellTime" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="XAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="XAxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Pole programming relative to the last programmed setpoint position">
        <CondWord Logical="and" Name="G" Range="110"/>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="X"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Pole programming relative to zero of current workpiece coordinate system">
        <CondWord Logical="and" Name="G" Range="111"/>
        <Macro Name="PolarCoordPoleXYZ" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="X"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Pole programming relative to the last valid pole">
        <CondWord Logical="and" Name="G" Range="112"/>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="X"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="AROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="ASCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="ROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="SCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Polar Interpolation">
        <CondState Logical="and" Name="INTERPOLATION" Value="POLAR"/>
        <CondState Logical="and" Name="ABS_INC" Value="INCREMENTAL"/>
        <Macro Name="PolarXIncValue" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Polar Interpolation">
        <CondState Logical="and" Name="INTERPOLATION" Value="POLAR"/>
        <Macro Name="PolarXValue" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="XAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="Y" Type="word" Description="MOTION: Y" Field="0">
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="YAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="YAxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Pole programming relative to the last programmed setpoint position">
        <CondWord Logical="and" Name="G" Range="110"/>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="Y"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Pole programming relative to zero of current workpiece coordinate system">
        <CondWord Logical="and" Name="G" Range="111"/>
        <Macro Name="PolarCoordPoleXYZ" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="Y"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Pole programming relative to the last valid pole">
        <CondWord Logical="and" Name="G" Range="112"/>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="Y"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="AROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="ASCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="ROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="SCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Cylindrical Interpolation">
        <CondState Logical="and" Name="INTERPOLATION" Value="CYLINDRICAL"/>
        <Macro Name="CAxisMotion" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="$ * 360 / PI / #CGT_CYL_DIA"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Polar Interpolation">
        <CondState Logical="and" Name="INTERPOLATION" Value="POLAR"/>
        <CondState Logical="and" Name="ABS_INC" Value="INCREMENTAL"/>
        <Macro Name="PolarYIncValue" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Polar Interpolation">
        <CondState Logical="and" Name="INTERPOLATION" Value="POLAR"/>
        <Macro Name="PolarYValue" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="YAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="Z" Type="word" Description="MOTION: Z" Field="0">
      <ConditionMacro Description="Lower working area limitation">
        <CondWord Logical="and" Name="G" Range="25"/>
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Upper working area limitation">
        <CondWord Logical="and" Name="G" Range="26"/>
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset (coarse offset)">
        <CondWord Logical="and" Name="G" Range="58"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset (fine offset)">
        <CondWord Logical="and" Name="G" Range="59"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Search for reference">
        <CondWord Logical="and" Name="G" Range="74"/>
        <Macro Name="ZAxisIncreMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Fixed point approach">
        <CondWord Logical="and" Name="G" Range="75"/>
        <Macro Name="ZAxisMachineRefMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Pole programming relative to the last programmed setpoint position">
        <CondWord Logical="and" Name="G" Range="110"/>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="yes">
          <Override  Type="text"  Value="Z"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Pole programming relative to zero of current workpiece coordinate system">
        <CondWord Logical="and" Name="G" Range="111"/>
        <Macro Name="PolarCoordPoleXYZ" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="Z"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Pole programming relative to the last valid pole">
        <CondWord Logical="and" Name="G" Range="112"/>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="Z"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="AMIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="AROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="ASCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Additive programmable work offset">
        <CondWord Logical="and" Name="ATRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable mirroring">
        <CondWord Logical="and" Name="MIRROR"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable rotation">
        <CondWord Logical="and" Name="ROT"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Programmable scaling">
        <CondWord Logical="and" Name="SCALE"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Absolute programmable work offset">
        <CondWord Logical="and" Name="TRANS"/>
        <Macro Name="SiemensFrameAxisArgument" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Polar Interpolation">
        <CondState Logical="and" Name="INTERPOLATION" Value="POLAR"/>
        <CondState Logical="and" Name="ABS_INC" Value="INCREMENTAL"/>
        <Macro Name="PolarZIncValue" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Polar Interpolation">
        <CondState Logical="and" Name="INTERPOLATION" Value="POLAR"/>
        <Macro Name="PolarZValue" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="ZAxisMotion" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <SuperGroup Name="M_Misc">
    <Group Name="M" Type="word" Description="MISCELLANEOUS: Programmed stop" Range="0" Field="0">
      <ConditionMacro Description="">
        <Macro Name="StopProgram" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="MISCELLANEOUS: Optional stop" Range="1" Field="0">
      <ConditionMacro Description="">
        <Macro Name="StopOptional" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="SUBROUTINES: End of program, main program (as M30)" Range="2" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];5"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];1"/>
        </Macro>
        <Macro Name="CancelShiftOffsets" Scan="no" AfterMotion="yes">
        </Macro>
        <Macro Name="RotationPlaneCancelReset" Scan="no" AfterMotion="yes">
        </Macro>
        <Macro Name="EndProgramRewindSpecial" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: CW spindle rotation" Range="3" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];3"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];1"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: CCW spindle rotation" Range="4" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleDir" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CCW"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="4"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];4"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];1"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: Spindle stop" Range="5" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];5"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];1"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="TOOLING: Tool change" Range="6" Field="0">
      <ConditionMacro Description="Call ToolChange subroutine if present otherwise calls ToolChange2 macro">
        <Macro Name="ToolChangeMachineSubroutine2" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="COOLANT: Coolant Mist" Range="7" Field="0">
      <ConditionMacro Description="">
        <Macro Name="CoolantMist" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="COOLANT: Coolant On" Range="8" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantFlood" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="COOLANT: Coolant Off" Range="9" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Optimizable" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CoolantOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="SUBROUTINES: End of subprogram" Range="17" Field="0">
      <ConditionMacro Description="Enters in SAVE procedure">
        <Macro Name="ReturnFromSub" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CallSubName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="P_PROG_RETURN"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: Active Spindle Orient and Turn Off" Range="19" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SpindleOrientLocal" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];5"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Positioning mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];2"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="SUBROUTINES: End of program, main program (as M2)" Range="30" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Macro Name="ActiveSpindleOnOff" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Variable Name="$P_SDIR[0]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SDIR[{#$P_MSNUM}];5"/>
        </Macro>
        <Variable Name="$P_SMODE[0]" Description="Speed control mode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="UpdateVariable" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_SMODE[{#$P_MSNUM}];1"/>
        </Macro>
        <Macro Name="RotationPlaneCancelReset" Scan="no" AfterMotion="yes">
        </Macro>
        <Macro Name="EndProgramRewindSpecial" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: Automatic gear change" Range="40" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: Gear step 1" Range="41" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: Gear step 2" Range="42" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: Gear step 3" Range="43" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: Gear step 4" Range="44" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="FEEDS &amp; SPEEDS: Gear step 5" Range="45" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="M" Type="word" Description="" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <SuperGroup Name="G_Prep">
    <Group Name="ANG" Type="word" Description="MOTION: Contour angle" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensPolarAngle" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="DWELL: Dwell time, preset" Range="4" Field="0">
      <ConditionMacro Description="Dwell Units Seconds">
        <CondWord Logical="and" Name="F"/>
        <Macro Name="DwellSeconds" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Dwell Units Revolutions">
        <CondWord Logical="and" Name="S"/>
        <Macro Name="DwellRevolutions" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Dwell Units Seconds">
        <CondWord Logical="and" Name="X"/>
        <Macro Name="DwellSeconds" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Apply Dwell Time">
        <Macro Name="DwellMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="CUTTER COMPENSATION: Tool radius compensation OFF" Range="40" Field="0">
      <ConditionMacro Description="Soft retraction with straight line">
        <CondWord Logical="and" Name="G" Range="148"/>
        <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="CutterCompOff" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Soft retraction with quadrant">
        <CondWord Logical="and" Name="G" Range="248"/>
        <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="CutterCompOff" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="Soft retraction with semicircle">
        <CondWord Logical="and" Name="G" Range="348"/>
        <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="CutterCompOff" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="CutterCompOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="CUTTER COMPENSATION: Tool radius compensation left of contour" Range="41" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="CutterCompLeft" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="CUTTER COMPENSATION: Tool radius compensation right of contour" Range="42" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Macro Name="CutterCompRight" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="SHIFT OFFSETS: Absolute programmable work offset (coarse offset)" Range="58" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$MC_FRAME_ADD_COMPONENTS" Range="1"/>
        <CondVariable Logical="and" Name="$MN_MM_FRAME_FINE_TRANS" Range="1"/>
        <Macro Name="SiemensG58G59" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="MessageMacro" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
          <Override  Type="text"  Value="Alarm 18312: Frame: fine shift not configured, $MN_MM_FRAME_FINE_TRANS and  $MC_FRAME_ADD_COMPONENTS must be TRUE"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="SHIFT OFFSETS: Additive programmable work offset (fine offset)" Range="59" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$MC_FRAME_ADD_COMPONENTS" Range="1"/>
        <CondVariable Logical="and" Name="$MN_MM_FRAME_FINE_TRANS" Range="1"/>
        <Macro Name="SiemensG58G59" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="FI"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="MessageMacro" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
          <Override  Type="text"  Value="Alarm 18312: Frame: fine shift not configured, $MN_MM_FRAME_FINE_TRANS and  $MC_FRAME_ADD_COMPONENTS must be TRUE"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MISCELLANEOUS: Search for reference" Range="74" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ReferencePoint" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MISCELLANEOUS: Fixed point approach" Range="75" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ReferencePoint" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Pole programming relative to the last programmed setpoint position" Range="110" Field="0">
      <ConditionMacro Description="Polar angle">
        <CondWord Logical="and" Name="AP"/>
        <Macro Name="PolarCoordPoleCurPos" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_RP * COS(#$P_AP)"  Units="0"/>
          <Override  Type="text"  Value="X"/>
        </Macro>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_RP * SIN(#$P_AP)"  Units="0"/>
          <Override  Type="text"  Value="Y"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="PolarCoordPoleCurPos" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Pole programming relative to zero of current workpiece coordinate system" Range="111" Field="0">
      <ConditionMacro Description="">
        <CondWord Logical="and" Name="AP"/>
        <Macro Name="PolarCoordPoleXYZ" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_RP * COS(#$P_AP)"  Units="0"/>
          <Override  Type="text"  Value="X"/>
        </Macro>
        <Macro Name="PolarCoordPoleXYZ" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_RP * SIN(#$P_AP)"  Units="0"/>
          <Override  Type="text"  Value="Y"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Pole programming relative to the last valid pole" Range="112" Field="0">
      <ConditionMacro Description="Polar angle">
        <CondWord Logical="and" Name="AP"/>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_RP * COS(#$P_AP)"  Units="0"/>
          <Override  Type="text"  Value="X"/>
        </Macro>
        <Macro Name="PolarCoordPoleIncXYZ" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$P_RP * SIN(#$P_AP)"  Units="0"/>
          <Override  Type="text"  Value="Y"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Soft approach and retracion approach direction defined by G41/G42" Range="140" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Soft approach and retracion approach direction to left of contour" Range="141" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Soft approach and retracion approach direction to right of contour" Range="142" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="MOTION: Soft approach and retracion approach direction tangent-dependent" Range="143" Field="0">
      <ConditionMacro Description="">
        <Macro Name="IgnoreMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G" Type="word" Description="" Field="0">
      <ConditionMacro Description="">
        <Macro Name="Unsupported" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="AMIRROR" Type="word" Description="TRANSFORMATION: Programmable mirroring)" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensAMIRROR" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ASCALE" Type="word" Description="TRANSFORMATION: Programmable scaling" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensASCALE" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="AROT" Type="word" Description="TRANSFORMATION: Programmable rotation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensAROT" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ATRANS" Type="word" Description="TRANSFORMATION: Additive programmable work offset" Field="0">
      <ConditionMacro Description="">
        <CondVariable Logical="and" Name="$MC_FRAME_ADD_COMPONENTS" Range="1"/>
        <Macro Name="SiemensATRANS" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="FI"/>
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="SiemensATRANS" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="MIRROR" Type="word" Description="TRANSFORMATION: Programmable mirroring" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensMIRROR" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ORISOL" Type="word" Description="TRANSFORMATION: Tool orientation in the workpiece coordinate system " Field="0">
      <ConditionMacro Description="Called in CYCLE809">
        <Macro Name="SetDfmtPrecision" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="12"  Units="0"/>
        </Macro>
        <Macro Name="SiemensORISOLAxisOrder" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="S_C_NR S_B_NR S_SP_NR"/>
        </Macro>
        <Macro Name="SiemensORISOL" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="$P_ORI_POS $P_ORI_SOL $P_ORI_STAT"/>
        </Macro>
        <Macro Name="SetDfmtPrecision" Scan="no" AfterMotion="yes">
          <Override  Type="value"  Value="4"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="ROT" Type="word" Description="TRANSFORMATION: Programmable rotation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensROT" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="SCALE" Type="word" Description="TRANSFORMATION: Programmable scaling" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensSCALE" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="TRANS" Type="word" Description="TRANSFORMATION: Programmable translation" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensTRANS" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <SuperGroup Name="Indirect_G_Prep">
    <Group Name="$P_BFRAME" Type="variable" Description="WORK OFFSETS: Channel-specific base frames" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensSetFrame2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_BFRAME $P_CHBFRAME[0]"/>
        </Macro>
        <Macro Name="SiemensUpdateActBframe" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$P_CHBFRAME" Type="variable" Description="WORK OFFSETS: Channel-specific base frames" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensUpdateActBframe" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$P_CYCFRAME" Type="variable" Description="TRANSFORMATION: Cycles" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$P_NCBFRAME" Type="variable" Description="WORK OFFSETS: Global base frames" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensUpdateActBframe" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$P_EXTFRAME" Type="variable" Description="WORK OFFSETS: External zero offset" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$P_IFRAME" Type="variable" Description="WORK OFFSETS: Current settable frame" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="no">
        </Macro>
        <Variable Name="$P_GG[8]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="-1"  Units="0"/>
        </Variable>
      </ConditionMacro>
    </Group>
    <Group Name="$P_PFRAME" Type="variable" Description="TRANSFORMATION: Current programmable frame" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$P_SETFRAME" Type="variable" Description="TRANSFORMATION: Preset actual value memory and scratching" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$P_TRAFRAME" Type="variable" Description="TRANFORMATION: Transformations" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$P_UBFR" Type="variable" Description="WORK OFFSETS: Channel-specific base frames" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensSetFrame2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_UBFR $P_CHBFR[0]"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="$P_WPFRAME" Type="variable" Description="TRANSFORMATION: Workpiece reference points" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SiemensUpdateActframe" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[7]" Type="variable" Description="CUTTER COMPENSATION: Tool radius compensation OFF - Indirect G40" Range="1" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Variable>
        <Macro Name="CutterCompOff" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[7]" Type="variable" Description="CUTTER COMPENSATION: Tool radius compensation left of contour - Indirect G41" Range="2" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Variable>
        <Macro Name="CutterCompLeft" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="G[7]" Type="variable" Description="CUTTER COMPENSATION: Tool radius compensation right of contour - Indirect G42" Range="3" Field="0">
      <ConditionMacro Description="">
        <Variable Name="$P_GG[7]" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Variable>
        <Macro Name="CutterCompRight" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <SuperGroup Name="CGTECH">
    <Group Name="BLANK" Type="word" Description="MISCELLANEOUS" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SetComponentDisableEnable" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CONNECT" Type="word" Description="MISCELLANEOUS" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConnectCompName" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="DOORS" Type="word" Description="MISCELLANEOUS" Field="0">
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="UNBLANK" Type="word" Description="MISCELLANEOUS" Field="0">
      <ConditionMacro Description="">
        <Macro Name="SetComponentDisableEnable" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CONNECT_TO" Type="word" Description="MISCELLANEOUS" Field="0">
      <ConditionMacro Description="">
        <Macro Name="ConnectToCompName" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="OPEN" Type="word" Description="MISCELLANEOUS" Field="0">
      <ConditionMacro Description="">
        <CondWord Logical="and" Name="DOORS"/>
        <Macro Name="SaveUnits" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UnitsMetric" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UAxisMachineMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="500"  Units="0"/>
        </Macro>
        <Macro Name="RestoreUnits" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="CLOSE" Type="word" Description="MISCELLANEOUS" Field="0">
      <ConditionMacro Description="">
        <CondWord Logical="and" Name="DOORS"/>
        <Macro Name="SaveUnits" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UnitsMetric" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="UAxisMachineMotion" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="RestoreUnits" Scan="no" AfterMotion="yes">
        </Macro>
      </ConditionMacro>
      <ConditionMacro Description="">
        <Macro Name="NullMacro" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
    <Group Name="PLAY_SOUND" Type="word" Description="MISCELLANEOUS: Play sound" Field="0">
      <ConditionMacro Description="Play a .wav file">
        <Macro Name="PlaySoundFile" Scan="no" AfterMotion="no">
        </Macro>
      </ConditionMacro>
    </Group>
  </SuperGroup>
  <Events>
    <Event Type="start_init">
      <EventSub Name="">
        <Macro Name="DefineDashAsAlphaNumeric" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="InverseWordValue" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value=":"/>
        </Macro>
        <Macro Name="SpindleSpeedCheckOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensGEOAXLogic" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="SiemensAXISLogic" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="DEBUG"/>
        </Macro>
        <Macro Name="SiemensAXISFallbackOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensFrameLogic" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </EventSub>
      <EventSub Name="1">
        <Macro Name="SetSubsystemID" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="1"/>
        </Macro>
        <Macro Name="SiemensCompToVcAxisMapping3" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </EventSub>
    </Event>
    <Event Type="conversion_init">
      <EventSub Name="">
        <Macro Name="AccelDecelLogic" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="ConcatenateStringErrorOption" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="ConversionInit" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="CycleMotionPlaneCheckOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="CycleDrillingAxisLogic" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="FunctionTypeMismatchOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="GetCurrentDate" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$A_YEAR $A_MONTH $A_DAY"/>
        </Macro>
        <Macro Name="GetCurrentTime" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$A_HOUR $A_MINUTE $A_SECOND"/>
        </Macro>
        <Macro Name="NewCycleLogic" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SiemensArgumentMismatchOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SubroutineOrderLogic" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="SyncNoWaitOption" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="TransformMappingOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
      </EventSub>
      <EventSub Name="1">
        <Macro Name="AdjustToolOffset" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#DefaultAdjustToolOffset"  Units="0"/>
        </Macro>
        <Macro Name="ApplyCircleMappingToTransform" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="ApplyRotationPlaneWithIjk2Abc" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="ActiveSpindleCompName" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="{#SpindleCompName[0]}"/>
        </Macro>
        <Macro Name="AutosetTableAxisFrames2" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="AutosetToolManOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="AutosetToolManCutCom840DVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP15"/>
        </Macro>
        <Macro Name="AutosetToolManCutCom840DVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP16"/>
        </Macro>
        <Macro Name="AutosetToolManCutCom840DVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP17"/>
        </Macro>
        <Macro Name="AutosetToolManCutCom840DVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP18"/>
        </Macro>
        <Macro Name="AutosetToolManLength840DVars2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP3 Z"/>
        </Macro>
        <Macro Name="AutosetToolManLength840DVars2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP4 Y"/>
        </Macro>
        <Macro Name="AutosetToolManLength840DVars2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP5 X"/>
        </Macro>
        <Macro Name="AutosetToolManLength840DVars2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP8 Z"/>
        </Macro>
        <Macro Name="AutosetToolManLengthIDs" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_TOOLND $P_TOOLD"/>
        </Macro>
        <Macro Name="AutosetToolManMisc840DVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP1 TYPE 0 120 510 710 240 5 6 7 200 9 10 11 12 13 14"/>
        </Macro>
        <Macro Name="AutosetToolManMisc840DVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP6 RADIUS"/>
        </Macro>
        <Macro Name="AutosetToolManMisc840DVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_TP2 TOOLID"/>
        </Macro>
        <Macro Name="AutosetToolManCutCom840DVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP6"/>
        </Macro>
        <Macro Name="AutosetToolManMisc840DVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_DP7 CORNER"/>
        </Macro>
        <Macro Name="CornerAutoAdjust" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="CornerMaxAdjustment" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0.03"  Units="0"/>
        </Macro>
        <Macro Name="CutterCompLookAhead" Scan="no" AfterMotion="no">
          <Override  Type="expression"  Value="#$MC_CUTCOM_MAXNUM_CHECK_BLOCKS "  Units="0"/>
        </Macro>
        <Macro Name="DynamicWorkOffsets" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="DynamicWorkOffsetsMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="EIARotaryLocalDisplay" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="EIARotaryMachineDisplay" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="ALL"/>
        </Macro>
        <Macro Name="EndLabelLoop" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="ENDLABEL"/>
        </Macro>
        <Macro Name="FrameAbcOffsetAdjust" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
        </Macro>
        <Macro Name="GetCommentString" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CommentString"/>
        </Macro>
        <Macro Name="Ijk2AnglesLogic" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="Ijk2AnglesDefaultFromTo" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="Ijk2AnglesAddOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="Ijk2AnglesVerticalRule" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="2"/>
        </Macro>
        <Macro Name="Ijk2AnglesPickSolution" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="1 2"/>
        </Macro>
        <Macro Name="Ijk2AnglesSaveSolutions" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="_Ijk2Angles_Rotary_1 _Ijk2Angles_Rotary_2  _Ijk2Angles_Angle_1 _Ijk2Angles_Angle_2 _Ijk2Angles_Angle_3 _Ijk2Angles_Angle_4 _Ijk2Angles_Solutions"/>
        </Macro>
        <Macro Name="Ijk2AnglesInput" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="IJK"/>
        </Macro>
        <Macro Name="OffsetCalcsDrivenAxes" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="X Y Z U W"/>
        </Macro>
        <Macro Name="OptiPathOptimizeCDC" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="PolarCoordZeroRadius" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Macro>
        <Macro Name="PoleDefinesCircleCenter" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="ProcessCutterComp" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="RapidInterpolationWarningOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="ReportExpressionErrorsOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="RestrictRotaryAxis" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="FIRST"/>
        </Macro>
        <Macro Name="RotaryControlPointOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="RotationPlaneSpecialOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="RpcpOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Macro>
        <Macro Name="RpcpMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="RtcpMode" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SetAxisVariableNames" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SetCyclePartSurface" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="-0.1"  Units="0"/>
        </Macro>
        <Macro Name="SetDfmtPrecision" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="8"  Units="0"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurTime $AC_TIME"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurToolType TOOL_TYPE"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurToolSubType Tool_Sub_Type"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurToolAlpha CurrentToolAlpha"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurTool CurrentToolNum"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurToolRadius $P_TOOLR"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SiemensAxisLocalPlus 0000000 $AA_IW"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SiemensAxisLocalPlus 0000000 $P_EP"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="SiemensAxisMachineMinus 0000000 $AA_IM"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurCDC CurCDC"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurAdjustedGageOffset $P_TOOLL[2] $P_TOOLL[3] $P_TOOLL[1]"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurSubName CurSubName"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurStackLevel $P_STACK"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurToolIndex $P_TOOLNO"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurToolIndex $TC_MPP6[9998,1]"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurToolIndex $A_INA[1]"/>
        </Macro>
        <Macro Name="SetDynamicVars" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="CurToolVectorLocal $P_TOOLO[0] $P_TOOLO[1] $P_TOOLO[2]"/>
        </Macro>
        <Macro Name="SetDynamicVarsMcdUnits" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SetDynamicVarsXAxisMultiplier" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
          <Override  Type="text"  Value="POWER "/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
          <Override  Type="text"  Value="MULTIPLY "/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
          <Override  Type="text"  Value="DIVIDE"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="2"  Units="0"/>
          <Override  Type="text"  Value="MOD"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
          <Override  Type="text"  Value="ADD"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
          <Override  Type="text"  Value="SUBTRACT"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="4"  Units="0"/>
          <Override  Type="text"  Value="BITWISE_AND"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="5"  Units="0"/>
          <Override  Type="text"  Value="BITWISE_XOR"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="6"  Units="0"/>
          <Override  Type="text"  Value="BITWISE_OR"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="7"  Units="0"/>
          <Override  Type="text"  Value="AND"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="8"  Units="0"/>
          <Override  Type="text"  Value="OR"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="9"  Units="0"/>
          <Override  Type="text"  Value="CONDITIONALS"/>
        </Macro>
        <Macro Name="SetMathOperatorPriority" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="10"  Units="0"/>
          <Override  Type="text"  Value="CONCAT"/>
        </Macro>
        <Macro Name="SiemensACTBFRMaskOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensAXISMappingOnOff" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensORISOL2Option" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SiemensORISOL2FrameOption" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="0"  Units="0"/>
        </Macro>
        <Macro Name="SiemensORISOL2SpindleOrient" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensPAROTToolsideIgnore" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="SiemensRotaryAngleConversion" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="FIRST 2 SECOND 3 SPINDLE 2"/>
        </Macro>
        <Macro Name="SiemensRotaryRanges2" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$TC_CARR30[1] $TC_CARR31[1] $TC_CARR32[1] $TC_CARR33[1]"/>
        </Macro>
        <Macro Name="TangentialCapture" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="TangentialControlType" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="TurnOnOffGagePivotOffset" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="1"  Units="0"/>
        </Macro>
        <Macro Name="WorkOffsetRelative" Scan="no" AfterMotion="no">
          <Override  Type="value"  Value="3"  Units="0"/>
        </Macro>
        <Macro Name="ZeroAxisDisplayDrivenAxes" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="X Y Z U W"/>
        </Macro>
        <Macro Name="BlockFinish" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="TextVariableSet" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_PROG[0] {#CurSubName}"/>
        </Macro>
        <Macro Name="TextVariableSet" Scan="no" AfterMotion="no">
          <Override  Type="text"  Value="$P_PROG_NAME[0] {#CurSubName}"/>
        </Macro>
      </EventSub>
    </Event>
    <Event Type="conversion_finish">
      <EventSub Name="">
        <Macro Name="ConversionFinish" Scan="no" AfterMotion="no">
        </Macro>
      </EventSub>
    </Event>
    <Event Type="block_init">
      <EventSub Name="">
        <Macro Name="BlockInit" Scan="no" AfterMotion="no">
        </Macro>
      </EventSub>
    </Event>
    <Event Type="block_finish">
      <EventSub Name="">
        <Macro Name="BlockFinish" Scan="no" AfterMotion="no">
        </Macro>
        <Macro Name="SiemensNurbsProcess" Scan="no" AfterMotion="no">
        </Macro>
      </EventSub>
    </Event>
  </Events>
  <Variables>
    <Variable Name="CurCDC" Type="value" System="1" Description="CDC *" Expand="off">
      <NumberType>real</NumberType>
      <Vacancy Current="false" Initial="false" />
      <Value>0</Value>
    </Variable>
  </Variables>
  <MacroModals>
    <MacroModal Name="mmCONTROLLER_TYPE"  Value="mmCTL_GENERIC"/>
    <MacroModal Name="mmTOLERANCE_VALUE"  Value="0.03"/>
    <MacroModal Name="mmORDER_OF_MATH_OPERATIONS"  Value="mmRULES_OF_PRECEDENCE"/>
    <MacroModal Name="mmDEFAULT_WORD"  Value=""/>
    <MacroModal Name="mmMAX_WIRE_ANGLE"  Value="30"/>
    <MacroModal Name="mmDEFAULT_VOLTAGE"  Value="mmON_TEXT"/>
    <MacroModal Name="mmUV_INCREMENTAL_XY"  Value="mmYES_TEXT"/>
    <MacroModal Name="mmXY_DRIVES_UV"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmWORK_TABLE_XY_OUT_PLANE"  Value="0"/>
    <MacroModal Name="mmDEFAULT_TOOL_COMP_ID"  Value="1"/>
    <MacroModal Name="mmTOOL_NUMBER_METHOD"  Value="mmTOOL_SELECT_ONLY"/>
    <MacroModal Name="mmTOOL_CHANGE_RETRACT_METHOD"  Value="mmTOOL_NO_RETRACT"/>
    <MacroModal Name="mmTOOL_CHANGE_CAUSE_CANCEL"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmTOOL_CHANGE_CAUSE_RAPID"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmDEFAULT_WORK_OFFSET"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmDEFAULT_WORK_INDEX"  Value="54"/>
    <MacroModal Name="mmDEFAULT_MOTION_TYPE"  Value="mmRAPID"/>
    <MacroModal Name="mmDEFAULT_MOTION_PLANE"  Value="mmMOTION_PLANE_XY"/>
    <MacroModal Name="mmDEFAULT_UNITS"  Value="mmUNITS_PROJECT"/>
    <MacroModal Name="mmDEFAULT_ABSINCR"  Value="mmABSOLUTE_MODE"/>
    <MacroModal Name="mmDEFAULT_FEEDMODE"  Value="mmUNITS_PER_MINUTE"/>
    <MacroModal Name="mmDEFAULT_FEEDRATE"  Value="508"/>
    <MacroModal Name="mmOUTPUT_INIT_SPINDLE_LOC"  Value="mmYES_TEXT"/>
    <MacroModal Name="mmRAPID_MOTION_CAUSE_CANCEL"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmLINEAR_MOTION_CAUSE_CANCEL"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmCW_MOTION_CAUSE_CANCEL"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmCCW_MOTION_CAUSE_CANCEL"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmRAPID_FEEDRATE_MOTION"  Value="mmRAPID_TEXT"/>
    <MacroModal Name="mmMAX_CUT_FEED_RATE"  Value="50800"/>
    <MacroModal Name="mmOUTPUT_PRECISION"  Value="mmFULL_PRECISION"/>
    <MacroModal Name="mmSPECIFIED_OUTPUT_PRECISION"  Value="3"/>
    <MacroModal Name="mmCIRCLE_CENTER_MODE"  Value="mmINCREMENTAL_MODE"/>
    <MacroModal Name="mmCIRCLE_INC_IJK_METHOD"  Value="mmINC_IJK_FROM_START"/>
    <MacroModal Name="mmPITCH_SPECIFIED_WITH_IJK"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmAPT_CIRCLE_OUTPUT"  Value="mmAPT_CIRCLE"/>
    <MacroModal Name="mmCYCLE_RETRACT_LEVEL"  Value="mmRETRACT_SPECIFIED_POINT_TEXT"/>
    <MacroModal Name="mmCYCLE_CLEARANCE_DISTANCE"  Value="50.8"/>
    <MacroModal Name="mmCYCLE_RAPID_METHOD"  Value="mmPART_SURFACE"/>
    <MacroModal Name="mmCYCLE_DEPTH_VALUE"  Value="mmABSOLUTE_MODE"/>
    <MacroModal Name="mmCYCLE_INCREMENTAL_DEPTH_VALUE"  Value="mmRELATIVE_TO_PART_SURFACE"/>
    <MacroModal Name="mmCYCLE_RAPID_VALUE"  Value="mmG_CODE_DEPENDENT"/>
    <MacroModal Name="mmCYCLE_INCREMENTAL_RAPID_VALUE"  Value="mmRELATIVE_TO_CYCLE_INITIAL_LEVEL"/>
    <MacroModal Name="mmCYCLE_CANCEL_CAUSE_RAPID"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmCYCLE_IGNORE_ROTARY"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmCYCLE_EXECUTE"  Value="mmON_MOTION"/>
    <MacroModal Name="mmA_AXIS_ROTARY_TYPE"  Value="mmLINEAR"/>
    <MacroModal Name="mmB_AXIS_ROTARY_TYPE"  Value="mmLINEAR"/>
    <MacroModal Name="mmC_AXIS_ROTARY_TYPE"  Value="mmLINEAR"/>
    <MacroModal Name="mmA2_AXIS_ROTARY_TYPE"  Value="mmLINEAR"/>
    <MacroModal Name="mmB2_AXIS_ROTARY_TYPE"  Value="mmLINEAR"/>
    <MacroModal Name="mmC2_AXIS_ROTARY_TYPE"  Value="mmLINEAR"/>
    <MacroModal Name="mmA3_AXIS_ROTARY_TYPE"  Value="mmLINEAR"/>
    <MacroModal Name="mmB3_AXIS_ROTARY_TYPE"  Value="mmLINEAR"/>
    <MacroModal Name="mmC3_AXIS_ROTARY_TYPE"  Value="mmLINEAR"/>
    <MacroModal Name="mmABSOLUTE_ROTARY_DIRECTION"  Value="mmSHORTEST_DISTANCE"/>
    <MacroModal Name="mmRTCP"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmRTCP_CONTOUR"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmRTCP_WITH_MOTION"  Value="mmYES_TEXT"/>
    <MacroModal Name="mmRTCP_USES"  Value="mmGAGE_SPINDLE_OFFSET"/>
    <MacroModal Name="mmCDC_ONOFF_METHOD"  Value="mmRAMP_ONOFF_METHOD"/>
    <MacroModal Name="mmCDC_ONOFF_MOTION"  Value="mmCUTTER_PLANE_MOTION_TEXT"/>
    <MacroModal Name="mmTYPE_OF_SUB_NAMES"  Value="mmTEXT_NAMES"/>
    <MacroModal Name="mmAUTO_SEQUENCE_NUMBERING"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmADD_SEQUENCE_NUMBER"  Value="mmNO_TEXT"/>
    <MacroModal Name="mmSEQUENCE_INCREMENT_VALUE"  Value="10"/>
    <MacroModal Name="mmWORD_VALUE_SPACING"  Value="mmYES_TEXT"/>
    <MacroModal Name="mmADD_DATETIME_STAMP"  Value="mmYES_TEXT"/>
    <MacroModal Name="mmADD_DATETIME_STAMP_LINE"  Value="1"/>
    <MacroModal Name="mmOUTPUT_FORMAT"  Value="mmWORD_FORMAT"/>
    <MacroModal Name="mmVNC_TIME_SLICE_VALUE"  Value="100"/>
    <MacroModal Name="mmVNC_OFFSET_X"  Value="0"/>
    <MacroModal Name="mmVNC_OFFSET_Y"  Value="0"/>
    <MacroModal Name="mmVNC_OFFSET_Z"  Value="0"/>
  </MacroModals>
  <SyntaxCheck>
    <VC>11110011100000000</VC>
    <User Use="on" Type="condition" Count="7">
      <Name>==</Name>
      <Name>LogicalNOT</Name>
      <Name>IF</Name>
      <Name>LogicalNOT</Name>
      <Name>UNTIL</Name>
      <Name>LogicalNOT</Name>
      <Name>WHILE</Name>
    </User>
    <User Use="on" Type="condition" Count="3">
      <Name>G25</Name>
      <Name>LogicalNOT</Name>
      <Name>S</Name>
    </User>
    <User Use="on" Type="condition" Count="3">
      <Name>G26</Name>
      <Name>LogicalNOT</Name>
      <Name>S</Name>
    </User>
  </SyntaxCheck>
</VcControl>
