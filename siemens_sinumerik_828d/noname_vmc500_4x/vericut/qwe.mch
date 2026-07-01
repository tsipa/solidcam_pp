<?xml version="1.0"?>
<VcMachine Version="9.6" Machine="qwe" Unit="millimeter">
  <Information>
    <InfoUserName>Ts</InfoUserName>
    <InfoDateTime>Tue Jun 30 17:02:48 2026</InfoDateTime>
    <InfoVericutVersion>9.6</InfoVericutVersion>
    <InfoBuildDate>September 10, 2025 </InfoBuildDate>
    <InfoLibraryDate>06/23/25</InfoLibraryDate>
  </Information>
  <PriorityType>single</PriorityType>
  <Collision>
  </Collision>
  <Component Name="Base"
   Subsystem="1"
   Type="base" Visible="machine" Enabled="on" Draw="shaded" XRGB="0x00A0A0A0">
    <Attach></Attach>
    <Position X="0" Y="0" Z="0"/>
    <Rotation I="0" J="0" K="0"/>
    <Appearance Name="Machine Component" Ambient="0.2" Diffuse="0.7" Reflect="0.2" Specular="1" Shininess="6" Translucency="1" XRGB="0x00A0A0A0" SurfaceTextureOn="off" SurfaceTextureID="0" SurfaceTextureScale="1" SurfaceTextureRot="0" SurfaceTextureColor="material"/>
    <STL Unit="millimeter" Normal="outward" Visible="on" Enabled="on" HasOpenSurface="off" XRGB="0x80000000">
      <File>I:\Solid\vmc500\vmc500_4x\vmc500_4x - atc-1.STL</File>
      <EdgeAngle>30</EdgeAngle>
      <CollTriTessTol CollTriTessTolAuto="on" CollTriTessTolVal="1"/>
      <ModelMatrix>
        <MatrixXAxis X="1" Y="0" Z="0"/>
        <MatrixYAxis X="0" Y="1" Z="0"/>
        <MatrixZAxis X="0" Y="0" Z="1"/>
        <MatrixOrigin X="0" Y="0" Z="0"/>
      </ModelMatrix>
    </STL>
  </Component>
  <Component Name="Z"
   Subsystem="1"
   Type="linear" Visible="machine" Enabled="on" Draw="shaded" XRGB="0x00A0A0A0">
    <Attach>Base</Attach>
    <Position X="0" Y="0" Z="0"/>
    <Rotation I="0" J="0" K="0"/>
    <Appearance Name="Machine Component" Ambient="0.2" Diffuse="0.7" Reflect="0.2" Specular="1" Shininess="6" Translucency="1" XRGB="0x00A0A0A0" SurfaceTextureOn="off" SurfaceTextureID="0" SurfaceTextureScale="1" SurfaceTextureRot="0" SurfaceTextureColor="material"/>
    <Link Axis="Z" PartSide="auto" Register="Z"
     RapidRate="5000" Accel="125" Decel="125" MaxLinearVelocity="5000" MaxCornerVelocity="600">
      <AxisPriority PriorityGroup="0" PriorityPos="1" InterpolatedPos="on" PriorityNeg="1" InterpolatedNeg="on"/>
    </Link>
    <STL Unit="millimeter" Normal="outward" Visible="on" Enabled="on" HasOpenSurface="off" XRGB="0x80000000">
      <File>I:\Solid\vmc500\vmc500_4x\vmc500_4x - spindle-1.STL</File>
      <EdgeAngle>30</EdgeAngle>
      <CollTriTessTol CollTriTessTolAuto="on" CollTriTessTolVal="1"/>
      <ModelMatrix>
        <MatrixXAxis X="1" Y="0" Z="0"/>
        <MatrixYAxis X="0" Y="1" Z="0"/>
        <MatrixZAxis X="0" Y="0" Z="1"/>
        <MatrixOrigin X="0" Y="0" Z="0"/>
      </ModelMatrix>
    </STL>
  </Component>
  <Component Name="Spindle"
   Subsystem="1"
   Type="spindle" Visible="machine" Enabled="on" Draw="shaded" XRGB="0x00A0A0A0">
    <Attach>Z</Attach>
    <Position X="0" Y="0" Z="0"/>
    <Rotation I="0" J="0" K="0"/>
    <Appearance Name="Machine Component" Ambient="0.2" Diffuse="0.7" Reflect="0.2" Specular="1" Shininess="6" Translucency="1" XRGB="0x00A0A0A0" SurfaceTextureOn="off" SurfaceTextureID="0" SurfaceTextureScale="1" SurfaceTextureRot="0" SurfaceTextureColor="material"/>
    <Link Axis="Z" PartSide="auto" Register="Spindle">
    </Link>
  </Component>
  <Component Name="Tool"
   Subsystem="1"
   Type="tool" Visible="all" Enabled="on" Draw="translucent" XRGB="0x00A0A0A0">
    <Attach>Spindle</Attach>
    <Position X="0" Y="0" Z="0"/>
    <Rotation I="0" J="0" K="0"/>
    <Appearance Name="Machine Component" Ambient="0.2" Diffuse="0.7" Reflect="0.2" Specular="1" Shininess="6" Translucency="1" XRGB="0x00A0A0A0" SurfaceTextureOn="off" SurfaceTextureID="0" SurfaceTextureScale="1" SurfaceTextureRot="0" SurfaceTextureColor="material"/>
    <Tool TurretIndex="1"/>
    <Link Axis="Z" PartSide="auto" Register="Tool">
    </Link>
  </Component>
  <Component Name="Y"
   Subsystem="1"
   Type="linear" Visible="machine" Enabled="on" Draw="shaded" XRGB="0x00A0A0A0">
    <Attach>Base</Attach>
    <Position X="0" Y="0" Z="0"/>
    <Rotation I="0" J="0" K="0"/>
    <Appearance Name="Machine Component" Ambient="0.2" Diffuse="0.7" Reflect="0.2" Specular="1" Shininess="6" Translucency="1" XRGB="0x00A0A0A0" SurfaceTextureOn="off" SurfaceTextureID="0" SurfaceTextureScale="1" SurfaceTextureRot="0" SurfaceTextureColor="material"/>
    <Link Axis="Y" PartSide="auto" Register="Y"
     RapidRate="5000" Accel="125" Decel="125" MaxLinearVelocity="5000" MaxCornerVelocity="600">
      <AxisPriority PriorityGroup="0" PriorityPos="1" InterpolatedPos="on" PriorityNeg="1" InterpolatedNeg="on"/>
    </Link>
  </Component>
  <Component Name="X"
   Subsystem="1"
   Type="linear" Visible="machine" Enabled="on" Draw="shaded" XRGB="0x00A0A0A0">
    <Attach>Y</Attach>
    <Position X="0" Y="0" Z="0"/>
    <Rotation I="0" J="0" K="0"/>
    <Appearance Name="Machine Component" Ambient="0.2" Diffuse="0.7" Reflect="0.2" Specular="1" Shininess="6" Translucency="1" XRGB="0x00A0A0A0" SurfaceTextureOn="off" SurfaceTextureID="0" SurfaceTextureScale="1" SurfaceTextureRot="0" SurfaceTextureColor="material"/>
    <Link Axis="X" PartSide="auto" Register="X"
     RapidRate="5000" Accel="125" Decel="125" MaxLinearVelocity="5000" MaxCornerVelocity="600">
      <AxisPriority PriorityGroup="0" PriorityPos="1" InterpolatedPos="on" PriorityNeg="1" InterpolatedNeg="on"/>
    </Link>
    <STL Unit="millimeter" Normal="outward" Visible="on" Enabled="on" HasOpenSurface="off" XRGB="0x80000000">
      <File>I:\Solid\vmc500\vmc500_4x\vmc500_4x - rotary_axis_housing-1.STL</File>
      <EdgeAngle>30</EdgeAngle>
      <CollTriTessTol CollTriTessTolAuto="on" CollTriTessTolVal="1"/>
      <ModelMatrix>
        <MatrixXAxis X="1" Y="0" Z="0"/>
        <MatrixYAxis X="0" Y="1" Z="0"/>
        <MatrixZAxis X="0" Y="0" Z="1"/>
        <MatrixOrigin X="0" Y="0" Z="0"/>
      </ModelMatrix>
    </STL>
    <STL Unit="millimeter" Normal="outward" Visible="on" Enabled="on" HasOpenSurface="off" XRGB="0x80000000">
      <File>I:\Solid\vmc500\vmc500_4x\vmc500_4x - setter_cover-1.STL</File>
      <EdgeAngle>30</EdgeAngle>
      <CollTriTessTol CollTriTessTolAuto="on" CollTriTessTolVal="1"/>
      <ModelMatrix>
        <MatrixXAxis X="1" Y="0" Z="0"/>
        <MatrixYAxis X="0" Y="1" Z="0"/>
        <MatrixZAxis X="0" Y="0" Z="1"/>
        <MatrixOrigin X="0" Y="0" Z="0"/>
      </ModelMatrix>
    </STL>
    <STL Unit="millimeter" Normal="outward" Visible="on" Enabled="on" HasOpenSurface="off" XRGB="0x80000000">
      <File>I:\Solid\vmc500\vmc500_4x\vmc500_4x - table-2.STL</File>
      <EdgeAngle>30</EdgeAngle>
      <CollTriTessTol CollTriTessTolAuto="on" CollTriTessTolVal="1"/>
      <ModelMatrix>
        <MatrixXAxis X="1" Y="0" Z="0"/>
        <MatrixYAxis X="0" Y="1" Z="0"/>
        <MatrixZAxis X="0" Y="0" Z="1"/>
        <MatrixOrigin X="0" Y="0" Z="0"/>
      </ModelMatrix>
    </STL>
  </Component>
  <Component Name="A"
   Subsystem="1"
   Type="rotary" Visible="machine" Enabled="on" Draw="shaded" XRGB="0x00A0A0A0" RotarySpin="off">
    <Attach>X</Attach>
    <Position X="0" Y="0" Z="0"/>
    <Rotation I="0" J="0" K="0"/>
    <Appearance Name="Machine Component" Ambient="0.2" Diffuse="0.7" Reflect="0.2" Specular="1" Shininess="6" Translucency="1" XRGB="0x00A0A0A0" SurfaceTextureOn="off" SurfaceTextureID="0" SurfaceTextureScale="1" SurfaceTextureRot="0" SurfaceTextureColor="material"/>
    <Link Axis="-X" PartSide="auto" Register="A"
     RapidRate="5000" Accel="125" Decel="125" MaxLinearVelocity="5000" MaxCornerVelocity="600">
      <AxisPriority PriorityGroup="0" PriorityPos="1" InterpolatedPos="on" PriorityNeg="1" InterpolatedNeg="on"/>
    </Link>
    <STL Unit="millimeter" Normal="outward" Visible="on" Enabled="on" HasOpenSurface="off" XRGB="0x80000000">
      <File>I:\Solid\vmc500\vmc500_4x\vmc500_4x - rotary_axis-2.STL</File>
      <EdgeAngle>30</EdgeAngle>
      <CollTriTessTol CollTriTessTolAuto="on" CollTriTessTolVal="1"/>
      <ModelMatrix>
        <MatrixXAxis X="1" Y="0" Z="0"/>
        <MatrixYAxis X="0" Y="1" Z="0"/>
        <MatrixZAxis X="0" Y="0" Z="1"/>
        <MatrixOrigin X="0" Y="0" Z="0"/>
      </ModelMatrix>
    </STL>
  </Component>
  <Component Name="Attach"
   Subsystem="1"
   Type="attach" Visible="machine" Enabled="on" Draw="shaded" XRGB="0x00A0A0A0">
    <Attach>A</Attach>
    <Position X="0" Y="0" Z="0"/>
    <Rotation I="0" J="0" K="0"/>
    <Appearance Name="Machine Component" Ambient="0.2" Diffuse="0.7" Reflect="0.2" Specular="1" Shininess="6" Translucency="1" XRGB="0x00A0A0A0" SurfaceTextureOn="off" SurfaceTextureID="0" SurfaceTextureScale="1" SurfaceTextureRot="0" SurfaceTextureColor="material"/>
  </Component>
  <Preview Image="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"/>
</VcMachine>
