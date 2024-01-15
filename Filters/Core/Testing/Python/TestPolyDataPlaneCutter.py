#!/usr/bin/env python
import vtk
from vtk.test import Testing
from vtk.util.misc import vtkGetDataRoot

VTK_DATA_ROOT = vtkGetDataRoot()

res = 50

# Create the RenderWindow, Renderers and both Actors
ren0 = vtk.vtkRenderer()
ren1 = vtk.vtkRenderer()
ren2 = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.SetMultiSamples(0)
renWin.AddRenderer(ren0)
renWin.AddRenderer(ren1)
renWin.AddRenderer(ren2)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

# Create a synthetic sphere
sphere = vtk.vtkSphereSource()
sphere.SetCenter(0.0, 0.0, 0.0)
sphere.SetRadius(0.25)
sphere.SetPhiResolution(res)
sphere.SetThetaResolution(2*res)
sphere.Update()
print("Num cells: ", sphere.GetOutput().GetNumberOfCells())

# The cut plane
plane = vtk.vtkPlane()
plane.SetOrigin(0, 0, 0)
plane.SetNormal(1, 1, 1)

# Now create the usual cutter
cutter = vtk.vtkCutter()
cutter.SetInputConnection(sphere.GetOutputPort())
cutter.SetCutFunction(plane)

cutterMapper = vtk.vtkPolyDataMapper()
cutterMapper.SetInputConnection(cutter.GetOutputPort())
cutterMapper.ScalarVisibilityOff()

cutterActor = vtk.vtkActor()
cutterActor.SetMapper(cutterMapper)
cutterActor.GetProperty().SetColor(1, 1, 1)
cutterActor.GetProperty().SetInterpolationToFlat()

# Throw in an outline
outline = vtk.vtkOutlineFilter()
outline.SetInputConnection(sphere.GetOutputPort())

outlineMapper = vtk.vtkPolyDataMapper()
outlineMapper.SetInputConnection(outline.GetOutputPort())

outlineActor = vtk.vtkActor()
outlineActor.SetMapper(outlineMapper)

# Accelerated cutter (uses a sphere tree, or vtkPolyDataPlaneCutter)
cut = vtk.vtkPlaneCutter()
cut.SetInputConnection(sphere.GetOutputPort())
cut.SetPlane(plane)

sCutterMapper = vtk.vtkPolyDataMapper()
sCutterMapper.SetInputConnection(cut.GetOutputPort())
sCutterMapper.ScalarVisibilityOff()

sCutterActor = vtk.vtkActor()
sCutterActor.SetMapper(sCutterMapper)
sCutterActor.GetProperty().SetColor(1, 1, 1)
sCutterActor.GetProperty().SetInterpolationToFlat()

# Specialized plane cutting for convex polygons
ncut = vtk.vtkPolyDataPlaneCutter()
ncut.SetInputConnection(sphere.GetOutputPort())
ncut.SetPlane(plane)
ncut.SetBatchSize(10)

snCutterMapper = vtk.vtkPolyDataMapper()
snCutterMapper.SetInputConnection(ncut.GetOutputPort())
snCutterMapper.ScalarVisibilityOff()

snCutterActor = vtk.vtkActor()
snCutterActor.SetMapper(snCutterMapper)
snCutterActor.GetProperty().SetColor(1, 1, 1)
snCutterActor.GetProperty().SetInterpolationToFlat()

outlineT = vtk.vtkOutlineFilter()
outlineT.SetInputConnection(sphere.GetOutputPort())

outlineMapperT = vtk.vtkPolyDataMapper()
outlineMapperT.SetInputConnection(outlineT.GetOutputPort())

outlineActorT = vtk.vtkActor()
outlineActorT.SetMapper(outlineMapperT)

# Time the execution of the usual cutter
cutter_timer = vtk.vtkExecutionTimer()
cutter_timer.SetFilter(cutter)
cutter.Update()
CT = cutter_timer.GetElapsedWallClockTime()
print("vtkCutter:", CT)

# Time the execution of the vtkPlaneCutter filter, including initial build
# (of the sphere tree, or convexity check)
sCutter_timer = vtk.vtkExecutionTimer()
sCutter_timer.SetFilter(cut)
cut.Update()
ST = sCutter_timer.GetElapsedWallClockTime()
print("vtkPlaneCutter (including internal structures build):", ST)

# Time the execution of the vtkPlaneCutter filter after modifying plane
plane.Modified()
cut.Update()
ST = sCutter_timer.GetElapsedWallClockTime()
print("vtkPlaneCutter (reuse cached internal structures):", ST)

# Time vtkPolyDataPlaneCutter
nCutter_timer = vtk.vtkExecutionTimer()
nCutter_timer.SetFilter(ncut)
ncut.Update()
SN = nCutter_timer.GetElapsedWallClockTime()
print("vtkPolyDataPlaneCutter:", SN)

# Compute normals on; attributes off (just to make sure
# these options are working).
ncut.ComputeNormalsOn()
ncut.InterpolateAttributesOff()
ncut.Update()
SN = nCutter_timer.GetElapsedWallClockTime()
print("vtkPolyDataPlaneCutter (with normals, no attributes):", SN)

# Finally, create some data to exercise the convexity check
cvxPData = vtk.vtkPolyData()
cvxPts = vtk.vtkPoints()
cvxPolys = vtk.vtkCellArray()
cvxPData.SetPoints(cvxPts)
cvxPData.SetPolys(cvxPolys)

cvxPts.SetNumberOfPoints(5)
cvxPts.SetPoint(0, 0,0,0)
cvxPts.SetPoint(1, 1,0,0)
cvxPts.SetPoint(2, 2,0,0)
cvxPts.SetPoint(3, 1,1,0)
cvxPts.SetPoint(4, 0,1,0)

cell = [0,1,3,4]
cvxPolys.InsertNextCell(4,cell)
cell = [1,2,3]
cvxPolys.InsertNextCell(3,cell)

print("Convex: (should be true): ", ncut.CanFullyProcessDataObject(cvxPData))
assert ncut.CanFullyProcessDataObject(cvxPData) == True

# Warp the quad
cvxPts.SetPoint(0,0.75,0.75,0)
cvxPts.Modified()

print("Convex: (should be false): ", ncut.CanFullyProcessDataObject(cvxPData))
assert ncut.CanFullyProcessDataObject(cvxPData) == False

# Add the actors to the renderer, set the background and size
ren0.AddActor(outlineActor)
ren0.AddActor(cutterActor)
ren1.AddActor(outlineActorT)
ren1.AddActor(sCutterActor)
ren2.AddActor(outlineActorT)
ren2.AddActor(snCutterActor)

ren0.SetBackground(0, 0, 0)
ren1.SetBackground(0, 0, 0)
ren2.SetBackground(0, 0, 0)
ren0.SetViewport(0, 0, 0.33, 1)
ren1.SetViewport(0.33, 0, 0.66, 1)
ren2.SetViewport(0.66, 0, 1, 1)
renWin.SetSize(900, 300)
ren0.ResetCamera()
ren1.ResetCamera()
ren2.ResetCamera()
iren.Initialize()

renWin.Render()
iren.Start()
# --- end of script --
