#!/usr/bin/python 

import sys, os
import string
import shutil
import itertools
import glob ##Unix style pathname pattern expansion
import time
import shlex, subprocess
from dictionaries import program_loc, img_folder, my_aet, hostID, local_port, clinical_aet, clinical_IP, clinical_port, remote_aet, remote_IP, remote_port

# ******************************************************************************
print '''
-----------------------------------------------------------
Runs batch Exam list to get Dicom Exams on a local folder based on list of 
Exam_list.txt(list of MRN StudyIDs DicomExam# )

Run on master folder: Z:\Cristina\Pipeline4Archive
where Z: amartel_data(\\srlabs)

usage:     python Get_Anonymized_DicomExam.py Exam_list.txt
    [INPUTS]    
        Exam_list.txt (required) sys.argv[1] 

% Copyright (C) Cristina Gallego, University of Toronto, 2012 - 2013
% April 26/13 - Created first version that queries StudyId based on the AccessionNumber instead of DicomExamNo
% Sept 18/12 -     Added additional options for retrieving only specific sequences (e.g T1 or T2)
% June 14/14 - Rename fun getDICOMS_pacs to test new pushed studies
-----------------------------------------------------------
'''
def get_only_filesindirectory(mydir):
     return [name for name in os.listdir(mydir) 
            if os.path.isfile(os.path.join(mydir, name))]
            
def getDICOMS_pacs(path_rootFolder, img_folder, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN, countImages=False):
        
    # Create fileout to print listStudy information
    # if StudyID folder doesn't exist create it
    os.chdir(str(img_folder))
    if not os.path.exists(str(StudyID)):
        os.makedirs(str(StudyID))

    os.chdir(str(StudyID))

    # if AccessionN folder doesn't exist create it
    if not os.path.exists(str(AccessionN)):
        os.makedirs(str(AccessionN))
    
    os.chdir(program_loc)
    cmd='findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
            -k 0008,0020="" -k 0008,0050='+AccessionN+' -k 0020,0011="" -k 0008,0052="SERIES" \
            -k 0020,000D="" -k 0020,000e="" -k 0020,1002="" -k 0008,0070="" \
            -aet '+my_aet+' -aec '+remote_aet+' '+remote_IP+' '+remote_port+' > '+ 'outcome'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' 
    
    # the DICOM query model is strictly hierarchical and the information model hierarchy is PATIENT - STUDY - SERIES - INSTANCE
    # Each query can only retrieve information at exactly one of these levels, and the unique keys of all higher levels must be provided as part of the query. In practice that means you first have to identify a patient, then you can identify studies for that patient, then you can check which series within one study exist and finally you could see which instances (DICOM objects, images) there are within one series. 
    # First findscu will retrive SERIES for a given STUDYID
#    cmd = 'findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
#    -k 0008,0020="" -k 0020,0010=' + ExamID + ' -k 0020,0011="" -k 0008,0052="SERIES" \
#	-k 0020,000D="" -k 0020,000e="" -k 0020,1002="" -k 0008,0070="" \
#	-aet ' + my_aet + ' -aec ' + remote_aet + ' ' + remote_IP + ' ' + remote_port+
#          
    print '\n---- Begin query with ' + remote_aet + ' by PatientID ....' ;
    print "cmd -> " + cmd
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()
    
    #################################################
    # 2nd-Part: # Required for pulling images.
    # Added by Cristina Gallego. July 2013
    ################################################
    imagepath = str(img_folder)+'/'+str(StudyID)+'/'+str(AccessionN)
    print 'imagepath: ', imagepath

     #################################################
    # Check mthat accession exists
    readQueryFile1 = open('outcome'+os.sep+'findscu_'+AccessionN+'_SERIES.txt' , 'r')
    readQueryFile1.seek(0)
    line = readQueryFile1.readline()
    print '---------------------------------------\n'
    ListOfExamsUID = []  
    ListOfSeriesUID = []
    ListOfSeriesID = []
    count = 0
    match = 0
    images_in_series = 0
    
    # write output to file sout
    seriesout =  imagepath+'_seriesStudy.txt'
    sout = open(seriesout, 'a')
    
    while ( line ) : 
        if '(0008,0020) DA [' in line:    #SerieDate
            item = line
            exam_date = item[item.find('[')+1:item.find(']')]        
            #print 'exam_date => ' + exam_date    
            line = readQueryFile1.readline()
            
        elif '(0010,0020) LO [' in line:    #patient_id
            item = line
            patient_id = item[item.find('[')+1:item.find(']')]        
            #print 'patient_id => ' + patient_id    
            line = readQueryFile1.readline()
            
        elif '(0010,0010) PN [' in line:    #patient_name
            item = line
            patient_name = item[item.find('[')+1:item.find(']')] # this need to be anonymized
            patient_name = "AnonName"
            #print 'patient_name => ' + patient_name    
            line = readQueryFile1.readline()
            
        elif '(0008,1030) LO [' in line:    #exam_description
            item = line
            exam_description = item[item.find('[')+1:item.find(']')]        
            #print 'exam_description => ' + exam_description
            line = readQueryFile1.readline()
            
        elif '(0020,000d) UI [' in line:    #exam_uid
            item = line
            exam_uid = item[item.find('[')+1:item.find(']')]        
            #print 'exam_uid => ' + exam_uid    
            ListOfExamsUID.append(exam_uid)
            line = readQueryFile1.readline()
            
        elif '(0008,0050) SH [' in line:    #exam_number
            item = line
            accession_number = item[item.find('[')+1:item.find(']')]        
            #print 'accession_number => ' + accession_number    
            line = readQueryFile1.readline()
            
        elif '(0008,103e) LO [' in line:    #series_description
            item = line
            series_description = item[item.find('[')+1:item.find(']')]        
            #print 'series_description => ' + series_description
            line = readQueryFile1.readline()
            
        elif '(0020,000e) UI [' in line:    #series_uid
            item = line
            series_uid = item[item.find('[')+1:item.find(']')]        
            #print 'series_uid => ' + series_uid
            ListOfSeriesUID.append(series_uid)
            line = readQueryFile1.readline()
                    
        elif '(0020,0011) IS [' in line:    #series_number
            item = line
            series_number = item[item.find('[')+1:item.find(']')]
            series_number = series_number.rstrip()
            series_number = series_number.lstrip()
            ListOfSeriesID.append(series_number)
            #print 'series_number => ' + series_number
            
            if(match == 0):  # first series so far
                match = 1
                print " \nAccessionN: %1s %2s %3s %4s %5s \n" % (accession_number, patient_name, patient_id, exam_date, exam_description)
                print >> sout, " \nAccessionN: %1s %2s %3s %4s %5s \n" % (accession_number, patient_name, patient_id, exam_date, exam_description)
                print " series: # %2s %3s %4s \n" % ('series_number', 'series_description', '(#Images)')
                print >> sout, " series: # %2s %3s %4s \n" % ('series_number', 'series_description', '(#Images)')

            line = readQueryFile1.readline()
        
#        elif '(0020,1002) IS [' in line:    #images_in_series
#            item = line
#            images_in_series = item[item.find('[')+1:item.find(']')]        
#            print 'images_in_series => ' + images_in_series
#            line = readQueryFile1.readline()
#            
        elif( (line.rstrip() == '--------') and (match == 1) ):
            if (countImages==True): # some servers don't return 0020,1002, so count the series
                os.chdir(str(program_loc))
                
                cmd = 'findscu -v -S -k 0009,1002="" -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="" \
                -k 0010,0020="" -k 0008,1030="" -k 0008,0020="" -k 0008,0050='+AccessionN+' -k 0020,0011="" -k 0008,0052="IMAGE" \
                -k 0020,000D="" -k 0020,000e='+series_uid+' -k 0020,0013="" -k 0020,0020="" -k 0008,0023="" -k 0008,0033="" -k 00028,0102="" \
                -aet ' + my_aet + ' -aec ' + remote_aet + ' ' + remote_IP + ' ' + remote_port + ' > outcome'+os.sep+'findscu_'+AccessionN+'_IMAGE.txt'
                
                print '\n---- Begin query number of images ' + remote_aet + ' ....' ;
                print "cmd -> " + cmd
                p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
                p1.wait()
                
                #The images are queried and result is saved in tmp\\findscu_SERIES."
                fileout_image = 'outcome'+os.sep+'findscu_'+AccessionN+'_IMAGE.txt'
                readQueryFile2 = open(fileout_image, 'r')
                readQueryFile2.seek(0) # Reposition pointer at the beginning once again
                im_line = readQueryFile2.readline()
                
                while ( im_line ) :
                    if '(0020,0013) IS [' in im_line: #image_number
                        item = im_line
                        image_number = item[item.find('[')+1:item.find(']')]
                        #print 'image_number => ' + image_number
                        images_in_series += 1 
                        
                    im_line = readQueryFile2.readline()    
                
                readQueryFile2.close()
            
                if( images_in_series > 1): 
                    plural_string = "s"
                else: plural_string = "" 
                    
                print ' series %2d: %3d %4s %5d image%s' % (int(count), int(series_number), series_description, int(images_in_series), plural_string)
                print >> sout, ' series %2d: %3d %4s %5d image%s' % (int(count), int(series_number), series_description, int(images_in_series), plural_string)
                  # ------------ FInish obtaining SERIES info  countImages==True
                readQueryFile2.close()
            else:
                print ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                print >> sout, ' series %2d: %3d %4s' % (int(count), int(series_number), series_description)
                # ------------ FInish obtaining SERIES info  countImages==False
                   
            line = readQueryFile1.readline()
            count += 1;
            images_in_series=0
        else:
            line = readQueryFile1.readline()
            
    readQueryFile1.close()
    sout.close()
    IDser = 0
    
    for IDseries in ListOfSeriesID:
        os.chdir(str(img_folder))
        print os.getcwd()
    
        # if ExamID folder doesn't exist create it    
        os.chdir(str(StudyID))
        os.chdir(str(AccessionN))
        if not os.path.exists('S'+str(ListOfSeriesID[int(IDser)])):
            os.makedirs('S'+str(ListOfSeriesID[int(IDser)]))
        
        os.chdir('S'+str(ListOfSeriesID[int(IDser)]))
        
        # Proceed to retrive images
        # query protocol using the DICOM C-FIND primitive. 
        # For Retrieval the C-MOVE protocol requires that all primary keys down to the hierarchy level of retrieve must be provided
        cmd = program_loc+os.sep+'movescu -S +P '+ local_port +' -k 0008,0052="IMAGE" -k 0020,000d=' + ListOfExamsUID[int(IDser)] + ' -k 0020,000e=' + ListOfSeriesUID[int(IDser)] + '\
        -aec ' + remote_aet + ' -aet ' + my_aet + ' -aem ' + my_aet + ' ' + remote_IP + ' ' + remote_port
        print cmd
            
        # Image transfer takes place over the C-STORE primitive (Storage Service Class). 
        # All of that is documented in detail in pa  rt 4 of the DICOM standard.
        p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
        p1.wait()
        
        # Go back - go to next 
        os.chdir(str(program_loc))    
        IDser += 1

        
    ########## END PULL #######################################
    return

########################### START ####################################
if __name__ == '__main__':
    # Get Root folder ( the directory of the script being run)
    path_rootFolder = os.path.dirname(os.path.abspath(__file__))
    print path_rootFolder
    
    if not os.path.exists('outcome'):
        os.makedirs('outcome')
    
    argc = len(sys.argv)
    if argc < 2 :
        print 'Not enough arguments are inputed. '
        print """
        usage:     python Get_Anonymized_Accession.py Exam_list.txt 
        [INPUTS]
            Exam_list.txt (required) sys.argv[1] 
        """
        exit() #if argc <= 2 | 0:
    else:        
            
        # Open filename list
        file_ids = open(sys.argv[1],"r")
        try:
            for fileline in file_ids:
                # Get the line: Study#, DicomExam#
                fileline = fileline.split()
                PatientID = fileline[0]
                StudyID = fileline[1]
                AccessionN = fileline[2]
                                
                print '\n\n---- batch Get Anonymized DicomExam -----------------'
                print 'PatientID -> "' + PatientID + '"'
                print 'StudyID -> "' + StudyID + '"'
                print 'AccessionN -> "' + AccessionN + '"'
                
                # Call each one of these functions
                # 1) Pull StudyId/AccessionN pair from pacs
                # 2) Annonimize StudyId/AccessionN pair from pacs
                getDICOMS_pacs(path_rootFolder, img_folder, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN, countImages=False)                        
            
        finally:
            file_ids.close()
    

