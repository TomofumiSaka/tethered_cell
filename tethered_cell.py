import os
import math
import csv
import datetime
from ij import IJ, ImagePlus, ImageStack
from ij.io import OpenDialog, Opener
from ij.measure import ResultsTable
from ij.gui import OvalRoi, Plot
from ij.plugin import MontageMaker, Duplicator
from ij.plugin.frame import RoiManager


def plotRotation(RoiNum, resultpath, t, x, y, RotationSpeed):
    # plot t-x, t-y, x-y, t-RotationSpeed and save plot+RoiNum.bmp
    txplot = Plot("x-t plot","time (s)", "x (pixel)", t, x)
    typlot = Plot("y-t plot","time (s)", "y (pixel)", t, y)
    xyplot = Plot("x-y plot", "x (pixel)", "y (pixel)", x, y)
    tspeedplot = Plot("Rotation speed-t plot","time (s)", "Rotaion Speed (Hz)", t, RotationSpeed)

    graphW = 1000
    graphH = 500
    txplot.setFrameSize(graphW, graphH)
    typlot.setFrameSize(graphW, graphH)
    xyplot.setFrameSize(graphW, graphH)
    tspeedplot.setFrameSize(graphW, graphH)

    #make plots as stack image
    tximp = txplot.getImagePlus()
    xyimp = xyplot.getImagePlus()
    tyimp = typlot.getImagePlus()
    tsimp = tspeedplot.getImagePlus()

    pstack = ImageStack(tximp.width,tximp.height)
    pstack.addSlice(tximp.getProcessor())
    pstack.addSlice(tyimp.getProcessor())
    pstack.addSlice(xyimp.getProcessor())
    pstack.addSlice(tsimp.getProcessor())
    pstackimp = ImagePlus("plots", pstack)

    pstackM = MontageMaker().makeMontage2(pstackimp, 2, 2, 2, 1, 4, 1, 0, False)
    #pstackM.show()
    IJ.saveAs(pstackM, "BMP", os.path.join(resultpath,"Plot" + str(RoiNum) + ".bmp"))

    tximp.close()
    xyimp.close()
    tyimp.close()
    tsimp.close()
    pstackM.close()

def tethered_cell(datafilepath, FrameNum=100, FrameRate=100.0, CCW=1):
    #parameter setting; frame rate (frame/sec); rotation speed threthold (Hz), frame rate
    #CCW = 1 : the motor rotation direction and the cell rotation direction on the image are same
    #CCW = -1: the motor rotation direction and the cell rotation direction on the image are different
    opener = Opener()
    imp = opener.openImage(datafilepath)
    resultpath = datafilepath[:-8] + "_tethered_cell_result"
    if os.path.lexists(resultpath) is False:
        os.mkdir(resultpath)
    rm = RoiManager().getInstance()

    #z projection; standard deviation
    IJ.run(imp, "Subtract Background...", "rolling=5 light stack")
    IJ.run(imp, "Median...", "radius=2 stack")
    IJ.run(imp, "Z Project...", "stop=500 projection=[Standard Deviation]")
    zimp = IJ.getImage()
    IJ.saveAs(zimp, "bmp", os.path.join(resultpath,"STD_DEV.bmp"))
    # pick up tethered cell
    IJ.setAutoThreshold(zimp, "MaxEntropy dark")
    IJ.run(zimp, "Convert to Mask", "")
    IJ.run("Set Measurements...", "area centroid bounding shape feret's limit redirect=None decimal=3")
    IJ.run(zimp, "Analyze Particles...", "size=30-Infinity circularity=0.88-1.00 show=Nothing display exclude clear include")
    zrt = ResultsTable.getResultsTable()
    IJ.saveAs("Results", os.path.join(resultpath,"RoiInfo.csv"))

    #tcX and tcY are xy coordinates of tethered cell, tcdia is outer diameter of rotating tethered cell
    tcX = []
    tcY = []
    tcdia =[]
    for i in range(zrt.getCounter()):
        tcX.append(zrt.getValue("X", i))
        tcY.append(zrt.getValue("Y", i))
        tcdia.append(zrt.getValue("Feret", i))

    #add ROI into stack image
    for i in range(zrt.getCounter()):
        rm.add(imp, OvalRoi(tcX[i] - tcdia[i]/2, tcY[i] - tcdia[i]/2, tcdia[i] + 1, tcdia[i] + 1), i)

    #analyze center of mass (XM, YM) tethered cell
    #calculate rotation speed by ellipse fitting
    #theta -pi ~ pi

    IJ.setAutoThreshold(imp, "Li")
    for RoiNum in range(rm.getCount()):
        t = []
        tempXM = []
        tempYM = []
        theta = []
        RotationSpeed = []
        tempArea = []
        imp.setRoi(rm.getRoi(RoiNum))
        tempimp = Duplicator().run(imp)
        IJ.run("Set Measurements...", "area mean center fit limit redirect=None decimal=3")
        rm.select(RoiNum)
        rt = rm.multiMeasure(imp)
        for i in range(FrameNum):
            tempArea.append(rt.getValue("Area1", i))

        if 0 in tempArea:
            continue

        for i in range(FrameNum):
            t.append((1/FrameRate)*i)
            tempXM.append(rt.getValue("XM1", i))
            tempYM.append(rt.getValue("YM1", i))

        for i in range(FrameNum):
            theta.append(rt.getValue("Angle1", i)/180.0*math.pi)

        for i in range(FrameNum):
            if i == 0:
                RotationSpeed.append(0)
            else:
                tempRS = [theta[i] - theta[i-1], theta[i] - theta[i-1] + math.pi, theta[i] - theta[i-1]-math.pi,  theta[i] - theta[i-1] + 2*math.pi,  theta[i] - theta[i-1] - 2*math.pi]
                tempRS = sorted(tempRS, key = lambda x :abs(x) )
                RotationSpeed.append(CCW*tempRS[0]/(2.0*math.pi)*FrameRate)

        # write csv
        # earch columns indicate 1:index, 2:time(sec), 3:X-coordinate of center of mass(pixel), 4:Y-coordinate of center of mass (pixel), 5:Angle(Radian), 6:Rotation Speed(Hz)
        with open(os.path.join(resultpath,"Roi" + str(RoiNum) + ".csv"), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Index", "time(s)", "X", "Y", "Angle(rad)", "Rotation Speed(Hz)"])
            for index in range(0, len(t)):
                writer.writerow([index, t[index], tempXM[index], tempYM[index], theta[index], RotationSpeed[index]])
        # plot x-y, t-x, t-y, t-rotation speed, save plot as bmp
        plotRotation(RoiNum, resultpath, t, tempXM, tempYM, RotationSpeed)
        IJ.saveAs(tempimp, "tiff", os.path.join(resultpath,"Roi" + str(RoiNum) + ".tiff"))
        rt.reset()

    # get analysis date and time
    dt = datetime.datetime.today()
    dtstr = dt.strftime("%Y-%m-%d %H:%M:%S")
    #write analysis setting

    with open(os.path.join(resultpath,"analysis_setting.csv"), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Analysis Date","frame number","frame rate","CCW direction", "Method","Auto threshold", "Subtruct Background", "Median filter"])
        writer.writerow([dtstr, FrameNum, FrameRate, CCW, "Ellipse", "Li", "5.0", "2"])

    #save zstack image and results, close all image and relusts
    savestack = imp.getStack()
    while savestack.getSize() > 30:
        savestack.deleteLastSlice()
    saveimp = ImagePlus("ihvideo", savestack)
    IJ.saveAs(saveimp,"tiff", os.path.join(resultpath,"all_range.tiff"))
    if rm.getCount() != 0:
        rm.runCommand("Save", os.path.join(resultpath, "Roi.zip"))

    zimp.close()
    imp.close()
    rm.close()
    rt.reset()
    zrt.reset()

if __name__ in ['__builtin__','__main__']:
    dialog = OpenDialog('Opend file')
    path = dialog.getPath()
    tethered_cell(path)

    IJ.log("analysis finished")
