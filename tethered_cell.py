import os
import math
import csv
import datetime
from ij import IJ, ImagePlus, ImageStack
from ij.io import OpenDialog, Opener
from ij.measure import ResultsTable
from ij.gui import OvalRoi, Plot, GenericDialog
from ij.plugin import MontageMaker, Duplicator
from ij.plugin.frame import RoiManager


def plotRotation(RoiNum, result_path, t, x, y, rotation_speed):
    # plot t-x, t-y, x-y, t-rotation_speed and save plot+RoiNum.bmp
    txplot = Plot('x-t plot','time (s)', 'x (pixel)', t, x)
    typlot = Plot('y-t plot','time (s)', 'y (pixel)', t, y)
    xyplot = Plot('x-y plot', 'x (pixel)', 'y (pixel)', x, y)
    tspeedplot = Plot('Rotation speed-t plot','time (s)', 'Rotaion Speed (Hz)', t, rotation_speed)

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
    pstackimp = ImagePlus('plots', pstack)

    pstackM = MontageMaker().makeMontage2(pstackimp, 2, 2, 2, 1, 4, 1, 0, False)
    #pstackM.show()
    IJ.saveAs(pstackM, 'BMP', os.path.join(result_path,'Plot' + str(RoiNum) + '.bmp'))

    tximp.close()
    xyimp.close()
    tyimp.close()
    tsimp.close()
    pstackM.close()

def tethered_cell(image_path, frame_number=100, frame_rate=100.0, CCW=1):
    """
    parameter setting; frame rate (frame/sec)

    CCW = 1 : the motor rotation direction and the cell rotation direction on the image are same
    CCW = -1: the motor rotation direction and the cell rotation direction on the image are different
    """
    opener = Opener()
    imp = opener.openImage(image_path)
    result_path = image_path + '_tethered_cell_result'
    if os.path.lexists(result_path) is False:
        os.mkdir(result_path)
    rm = RoiManager().getInstance()

    #z projection; standard deviation
    IJ.run(imp, 'Subtract Background...', 'rolling=5 light stack')
    IJ.run(imp, 'Median...', 'radius=2 stack')
    IJ.run(imp, 'Z Project...', 'stop=500 projection=[Standard Deviation]')
    zimp = IJ.getImage()
    IJ.saveAs(zimp, 'bmp', os.path.join(result_path,'STD_DEV.bmp'))
    # pick up tethered cell
    IJ.setAutoThreshold(zimp, 'MaxEntropy dark')
    IJ.run(zimp, 'Convert to Mask', '')
    IJ.run('Set Measurements...', "area centroid bounding shape feret's limit redirect=None decimal=3")
    IJ.run(zimp, 'Analyze Particles...', 'size=30-Infinity circularity=0.88-1.00 show=Nothing display exclude clear include')
    zrt = ResultsTable.getResultsTable()
    IJ.saveAs('Results', os.path.join(result_path,'RoiInfo.csv'))

    #tcX and tcY are xy coordinates of tethered cell, tcdia is outer diameter of rotating tethered cell
    #add ROI into stack image
    for i in range(zrt.getCounter()):
        tcX = zrt.getValue('X', i)
        tcY = zrt.getValue('Y', i)
        tcdia = zrt.getValue('Feret', i)
        rm.add(imp, OvalRoi(tcX - tcdia/2.0, tcY - tcdia/2.0, tcdia + 1, tcdia + 1), i)

    #calculate rotation speed by ellipse fitting
    IJ.setAutoThreshold(imp, 'Li')
    for RoiNum in range(rm.getCount()):
        t = []
        XM = []
        YM = []
        theta = []
        rotation_speed = []
        area = []
        imp.setRoi(rm.getRoi(RoiNum))
        cropped_imp = Duplicator().run(imp)
        IJ.run('Set Measurements...', 'area mean center fit limit redirect=None decimal=3')
        rm.select(RoiNum)
        rt = rm.multiMeasure(imp)

        # check cell is present while analysis. Don't a cell gose anywhare?
        for i in range(frame_number):
            area.append(rt.getValue('Area1', i))
        if 0 in area:
            continue

        for i in range(frame_number):
            t.append((1/frame_rate)*i)
            XM.append(rt.getValue('XM1', i))
            YM.append(rt.getValue('YM1', i))
            theta.append(rt.getValue('Angle1', i)/180.0*math.pi)  # convert to radian

            if i == 0:
                rotation_speed.append(0)
            else:
                # phase treatment, theta should be -pi ~ pi
                tempRS = [theta[i] - theta[i-1],
                          theta[i] - theta[i-1] + math.pi,
                          theta[i] - theta[i-1] - math.pi,
                          theta[i] - theta[i-1] + 2*math.pi,
                          theta[i] - theta[i-1] - 2*math.pi]
                tempRS = sorted(tempRS, key = lambda x :abs(x) )
                rotation_speed.append(CCW*tempRS[0]/(2.0*math.pi)*frame_rate)

        # write csv
        # earch columns indicate 1:index, 2:time(sec), 3:X-coordinate of center of mass(pixel), 4:Y-coordinate of center of mass (pixel), 5:Angle(Radian), 6:Rotation Speed(Hz)
        with open(os.path.join(result_path,'Roi' + str(RoiNum) + '.csv'), 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['Index', 'time(s)', 'X', 'Y', 'Angle(rad)', 'Rotation Speed(Hz)'])
            for i in range(len(t)):
                writer.writerow([i, t[i], XM[i], YM[i], theta[i], rotation_speed[i]])
        # plot x-y, t-x, t-y, t-rotation speed, save plot as bmp
        plotRotation(RoiNum, result_path, t, XM, YM, rotation_speed)
        IJ.saveAs(cropped_imp, 'tiff', os.path.join(result_path,'Roi' + str(RoiNum) + '.tiff'))
        rt.reset()

    # get analysis date and time
    dt = datetime.datetime.today()
    dtstr = dt.strftime('%Y-%m-%d %H:%M:%S')

    # wtite analysis setting
    with open(os.path.join(result_path,'analysis_setting.csv'), 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['Analysis Date','frame number','frame rate','CCW direction', 'Method','Auto threshold', 'Subtruct Background', 'Median filter'])
        writer.writerow([dtstr, frame_number, frame_rate, CCW, 'Ellipse', 'Li', '5.0', '2'])

    # save roi
    if rm.getCount() != 0:
        rm.runCommand('Save', os.path.join(result_path, 'Roi.zip'))

    zimp.close()
    imp.close()
    rm.close()
    zrt.reset()

if __name__ in ['__builtin__','__main__']:
    # ask file path via dialog
    open_file_dialog = OpenDialog('Opend file')
    path = open_file_dialog.getPath()

    # ask parameter via dialog
    parameter_dialog = GenericDialog('Parameter setting')
    parameter_dialog.addNumericField('Frame number', 100, 1)
    parameter_dialog.addNumericField('Frame rate (frame/s)', 100, 1)
    parameter_dialog.addChoice('Are motor rotation direction \n and cell rotation on image same? ', 
                               ['Same', 'Different'], 'Same')
    parameter_dialog.showDialog()
    frame_number = int(parameter_dialog.getNextNumber())
    frame_rate = 100.0
    choice = parameter_dialog.getNextChoice()
    if choice == 'Same':
        CCW = 1
    else:
        CCW = -1
    tethered_cell(path, frame_number, frame_rate, CCW)

    IJ.log('analysis finished')
