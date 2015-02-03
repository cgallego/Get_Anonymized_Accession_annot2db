#!/usr/bin/python 
import sys, os
import string
import shutil
import itertools
import glob ##Unix style pathname pattern expansion
import time
import shlex, subprocess
import SQL, query
from dictionaries import data_loc, program_loc, my_aet, hostID, local_port, clinical_aet, clinical_IP, clinical_port, remote_aet, remote_IP, remote_port

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

-----------------------------------------------------------
'''
def update_table(PatientID, StudyID, accession):
    """
    Runs code for a single accession number. Assumes that DICOM images are 
    already on the local hard drive, in a folder with the name as the accesion 
    number, in data_loc.
    """
    accessnum=str(accession)
    exam_loc=data_loc+'/'+accessnum
    query.queries(accessnum)  
    
    try:
        SQL.run_code(accessnum, exam_loc)
        try:
            if os.path.isdir(exam_loc):
                shutil.rmtree(exam_loc)    #os.rmdir(StudyNo)    #remove    # removedirs
        except ValueError:
            print "Deleting a Directory is problematic."    
            
    except Exception as e:
        os.chdir(program_loc)
        fil=open('Errors.txt','a')
        fil.write(PatientID+'\t'+StudyID+'\t'+accessnum+'\t'+str(e)+'\n')
        fil.close()
        print "Error. Please check Errors.txt for more details."
    return
    
    
def get_only_filesindirectory(mydir):
     return [name for name in os.listdir(mydir) 
            if os.path.isfile(os.path.join(mydir, name))]
            
def check_pacs(path_rootFolder, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN):
    print '\n--------- QUERY Suject: "' + PatientID + '" in "' + remote_aet + '" from "'+ my_aet + '" ----------'
    print "First: Checking whether wanted exam is archived on 'MRI_MARTEL'.\n"
    
    cmd=program_loc+os.sep+'findscu -v -S -k 0008,0020="" -k 0010,0010="" -k 0010,0020="" -k 0008,0018="" -k 0008,103e="" -k 0020,000e="" '+\
            '-k 0008,0050='+AccessionN+' -k 0008,0052="SERIES" \
        -aet '+my_aet+' -aec '+remote_aet+' '+remote_IP+' '+remote_port+' > '+ 'checkdata'+os.sep+'checkdata_'+AccessionN+'.txt' 
        
    print '\n---- Begin query with ' + remote_aet + ' by PatientID ....' ;
    print "cmd -> " + cmd
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()
    
    #################################################
    # Check mthat accession exists
    readQueryFile1 = open('checkdata'+os.sep+'checkdata_'+AccessionN+'.txt' , 'r')
    readQueryFile1.seek(0)
    line = readQueryFile1.readline()
    ListOfSeries = []
    while ( line ) : # readQueryFile1.readlines()):
        #print line
        if '(0008,0020) DA [' in line: #(0020,000d) UI
            lineStudyDate = line
            item = lineStudyDate
            pullStudyDate = item[item.find('[')+1:item.find(']')]
            
            nextline =  readQueryFile1.readline(),
            
            if '(0008,0050) SH' in nextline[0]:    # Filters by Modality MR
                item = nextline[0]
                newAccessionN = item[item.find('[')+1:item.find(']')]
            
            nextline =  readQueryFile1.readline(),
            while ( '(0008,103e) LO' not in nextline[0]) : #(0008,1030) LO 
                nextline = readQueryFile1.readline(),
            
            item = nextline[0]
            pullExamsDescriptions = item[item.find('[')+1:item.find(']')]
            print 'MRStudyDate => ' + pullStudyDate
            print 'newAccessionNumber => ' + newAccessionN
            print 'pullExamsDescriptions => ' + pullExamsDescriptions
                            
            '''---------------------------------------'''
            ListOfSeries.append([pullStudyDate, newAccessionN, pullExamsDescriptions])
            line = readQueryFile1.readline()
        else:
            line = readQueryFile1.readline()
    
    #################################################
    # Added: User input to pull specific Exam by Accession
    # Added by Cristina Gallego. April 26-2013            
    #################################################
    iExamPair=[]    
    flagfound = 1
    for iExamPair in ListOfSeries: # iExamID, iExamUID in ListOfExamsUID: #
        SelectedAccessionN = iExamPair[1]
        str_count = '';
        
        if SelectedAccessionN.strip() == AccessionN.strip():
            flagfound = 0
        
    if flagfound == 1:
        print "\n===============\n"
        print 'Accession number not found in '+remote_aet+' - Proceed with retrival'
        print "\n===============\n"
    else:
        print "\n===============\n"
        os.chdir(program_loc)
        fil=open('checkdata'+os.sep+'Errors_check.txt','a')
        fil.write(PatientID+'\t'+StudyID+'\t'+str(AccessionN)+'\tAccession number found in '+remote_aet+'\n')
        fil.close()
        sys.exit('Accession number found in '+remote_aet)
        
    return
        
def pull_pacs(path_rootFolder, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN):
    print 'EXECUTE DICOM/Archive Commands ...'
    print 'Query,  Pull,  Anonymize, Push ...'
    
    print '\n--------- QUERY Suject (MRN): "' + PatientID + '" in "' + clinical_aet + '" from "'+ my_aet + '" ----------'
    
    cmd = program_loc+os.sep+'findscu -v -P -k 0008,1030="" -k 0008,103e="" -k 0010,0010="" -k 0010,0020="' + PatientID + 'SHSC*''"\
    -k 0008,1030="" -k 0008,0052="STUDY" -k 0008,0020="" -k 0020,0010="" -k 0008,0050="*" \
    -k 0008,0060="" -k 0020,0011="" -k 0020,000D= -k 0020,1002="" -aet ' + my_aet + \
    ' -aec ' + clinical_aet + ' ' + clinical_IP + ' ' + clinical_port + ' > ' + path_rootFolder +os.sep+'querydata'+os.sep+PatientID+'_querydata_'+AccessionN+'.txt'     #142.76.62.102

    print '\n---- Begin query with ' + clinical_aet + ' by PatientID ....' ;
    print "cmd -> " + cmd
    p1 = subprocess.Popen(cmd, shell=True,   stdin=subprocess.PIPE)
    p1.wait()
    
    readQueryFile1 = open('querydata'+os.sep+PatientID+'_querydata_'+AccessionN+'.txt', 'r')
    readQueryFile1.seek(0)
    line = readQueryFile1.readline()
    print
    print '---------------------------------------'
    ListOfExams = []
    ListOfExamsUID = [] ; 
    ListOfExamsID = []
    ListOfExamsDescriptions = []
    ListOfExamDates = []
    while ( line ) : # readQueryFile1.readlines()):
        # found instance of exam
        #print line
        if '(0008,0020) DA [' in line: #(0020,000d) UI
            lineStudyDate = line
            item = lineStudyDate
            pullStudyDate = item[item.find('[')+1:item.find(']')]
            
            nextline =  readQueryFile1.readline(),
            
            if '(0008,0050) SH' in nextline[0]:    # Filters by Modality MR
                item = nextline[0]
                newAccessionN = item[item.find('[')+1:item.find(']')]
                                
        if '(0008,0060) CS [MR]' in line:    # Filters by Modality MR
            '''---------------------------------------'''
            nextline =  readQueryFile1.readline(),
            while ( 'StudyDescription' not in nextline[0]) : #(0008,1030) LO 
                nextline = readQueryFile1.readline(),
            
            item = nextline[0]
            pullExamsDescriptions = item[item.find('[')+1:item.find(']')]
            print 'MRStudyDate => ' + pullStudyDate
            print 'newAccessionNumber => ' + newAccessionN
            print 'pullExamsDescriptions => ' + pullExamsDescriptions
                            
            '''---------------------------------------'''
            nextline = readQueryFile1.readline(),
            while ( 'StudyInstanceUID' not in nextline[0]) : #(0020,000d) UI
                nextline = readQueryFile1.readline(),
                
            item = nextline[0] 
            pullStudyUID = item[item.find('[')+1:item.find(']')]        
            print 'pullStudyUID => ' + pullStudyUID    
            print '\n'            
            
                        
            '''---------------------------------------'''
            ListOfExams.append([pullStudyDate, newAccessionN, pullExamsDescriptions, pullStudyUID])
            line = readQueryFile1.readline()
        else:
            line = readQueryFile1.readline()
            
    readQueryFile1.close()
    print ListOfExams
    
    #################################################
    # Added: User input to pull specific Exam by Accession
    # Added by Cristina Gallego. April 26-2013            
    #################################################
    iExamPair=[]    
    flagfound = 1
    for iExamPair in ListOfExams: # iExamID, iExamUID in ListOfExamsUID: #
        SelectedAccessionN = iExamPair[1]
        SelectedExamUID = iExamPair[3]
        
        print AccessionN, SelectedAccessionN
        str_count = '';
        
        if SelectedAccessionN.strip() == AccessionN.strip():
            flagfound = 0
            for k in range(0,len(AccessionN.strip())):
                if SelectedAccessionN[k] == AccessionN[k]:
                    str_count = str_count+'1'
                            
            print len(AccessionN)
            print len(str_count)
            if( len(AccessionN) == len(str_count)):
                print "\n===============\n SelectedAccessionN, SelectedExamUID"
                iAccessionN = SelectedAccessionN
                iExamUID = SelectedExamUID
                print iAccessionN, iExamUID
                print "\n===============\n"
                break
    if flagfound == 1:
        os.chdir(program_loc)
        fil=open('outcome'+os.sep+'Errors_pull.txt','a')
        fil.write(PatientID+'\t'+StudyID+'\t'+str(AccessionN)+'\tAccession number not found in AS0SUNB\n')
        fil.close()
        print "\n===============\n"
        sys.exit("Error. Accession number not found in AS0SUNB.")
                        
    
    # Create fileout to print listStudy information
    # if StudyID folder doesn't exist create it        
    if not os.path.exists(path_rootFolder+os.sep+str(StudyID)):
        os.makedirs(path_rootFolder+os.sep+str(StudyID))
     
    os.chdir(path_rootFolder+os.sep+str(StudyID))
     
    # if AccessionN folder doesn't exist create it        
    if not os.path.exists(str(AccessionN)):
        os.makedirs(str(AccessionN))
        
    os.chdir(str(path_rootFolder))    
    
    #################################################
    # 2nd-Part: # Required for pulling images.
    # Added by Cristina Gallego. July 2013            
    #################################################
    writeRetrieveFile1 = open('outcome'+os.sep+'oRetrieveExam.txt', 'w')
    readRetrieveFile1 = open('outcome'+os.sep+'RetrieveExam.txt', 'r')
    print "Read original tags from RetrieveExam.txt. ......"
    readRetrieveFile1.seek(0)
    line = readRetrieveFile1.readline()
    outlines = ''
    
    while ( line ) : # readRetrieveFile1.readlines()):
        if '(0020,000d) UI' in line:    #StudyUID
            #print line, 
            fakeStudyUID = line[line.find('[')+1:line.find(']')]        
            print 'fakeStudyUID => ' + fakeStudyUID 
            line = line.replace(fakeStudyUID, iExamUID)
            outlines = outlines + line
            line = readRetrieveFile1.readline()
        else:
            outlines = outlines + line
            line = readRetrieveFile1.readline()
    
    writeRetrieveFile1.writelines(outlines)
    writeRetrieveFile1.close()
    readRetrieveFile1.close()        
            
    readRetrieveFile2 = open('outcome'+os.sep+'oRetrieveExam.txt', 'r')
    print "Updated tags from oRetrieveExam.txt. ......"
    for line in readRetrieveFile2.readlines(): # failed to print out ????
        print line,
    readRetrieveFile2.close()
    
    print '---------------------------------------'
    print os.path.isfile('dump2dcm.exe')    
    cmd = program_loc+os.sep+'dump2dcm outcome'+os.sep+'oRetrieveExam.txt outcome'+os.sep+'RetrieveExam.dcm' #r'dump2dcm
    print 'cmd -> ' + cmd
    print 'Begin dump to dcm ....' ;
    os.system(cmd)
    print 'outcome'+os.sep+'RetrieveExam.dcm is formed for pulling image from remote_aet.'
    print
    
    # Now Create a subfolder : AccessionN to pull images .
    os.chdir(path_rootFolder+os.sep+str(StudyID)+os.sep+str(AccessionN))
    
    ########## START PULL #######################################        
    print 'Pulling images to cwd: ' + os.getcwd()
    cmd = program_loc+os.sep+'movescu -v -P +P ' + local_port + ' -aem ' + my_aet + ' -aet ' + my_aet + ' -aec ' + clinical_aet \
    + ' ' + clinical_IP + ' ' + clinical_port + ' ' + path_rootFolder+os.sep+'outcome'+os.sep+'RetrieveExam.dcm ' 

    print 'cmd -> ' + cmd
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()
    ########## END PULL #######################################
    
    print 'Next, to group "raw" image files into a hierarchical. ...'
    imagepath = path_rootFolder+os.sep+str(StudyID)+os.sep+str(AccessionN) + '\\MR*.*'
    print 'imagepath: ', imagepath

    #################################################################
    # Anonymize/Modify images.                      
    # (0020,000D),StudyUID  (0020,000e),SeriesUID                   #
    # (0010,0010),PatientName/ID                                    #
    # (0012,0021),"BRCA1F"  (0012,0040),StudyNo                     #
    ###########################################
    os.chdir(str(program_loc))
    
    # Group all image files into a number of series for StudyUID/SeriesUID generation.
    cmd = 'dcmdump +f -L +F +P "0020,000e" +P "0020,0011" "' + imagepath + '" > outcome'+os.sep+'pulledDicomFiles.txt'  
    print 'cmd -> ' + cmd
    print 'Begin SortPulledDicom ....' ;
    lines = os.system(cmd) 
        
    readPulledFiles = open('outcome'+os.sep+'pulledDicomFiles.txt', 'r')
    
    print '---------------------------------------'
    ListOfSeriesGroup    = [] ; # [SeriesNo, SeriesUID] # SeriesNumber
    ListOfSeriesGroupRev = [] ; # [SeriesUID, SeriesNo]     
    ListOfSeriesPairs    = [] ; # [imageFn, SeriesUID]
    #ListOfExamsID = []
    outlines = ""
    nextline = readPulledFiles.readline()
    while ( nextline ) : # readPulledFiles.readlines()):
        if 'dcmdump' in nextline:   #Modality
            item = nextline; #[0] 
            imageFn = item[item.find(')')+2 : item.find('\n')]      
            
            nextline = readPulledFiles.readline() # ( 'SeriesNumber' : #(0020,0011) IS
            item = nextline; #[0] 
            SeriesNo = item[item.find('[')+1:item.find(']')]
            
            nextline =  readPulledFiles.readline() # ( 'SeriesInstanceUID' :    #(0020,000e) SH
            item = nextline; #[0]
            SeriesUID = item[item.find('[')+1:item.find(']')]
                
            '''---------------------------------------'''
            ListOfSeriesGroup.append([SeriesNo, SeriesUID])
            ListOfSeriesGroupRev.append([SeriesUID, SeriesNo])
            ListOfSeriesPairs.append([imageFn, SeriesUID])
            
            nextline = readPulledFiles.readline()
        else:
            nextline = readPulledFiles.readline()
    readPulledFiles.close()
    
    print "\n************************************************"
    print 'ListOfSeriesGroup'
    print ListOfSeriesGroup
    
    print 'ListOfSeriesGroup'
    ListOfSeriesGroupRev
    
    print 'ListOfSeriesGroup'
    ListOfSeriesPairs
    
    # Make a compact dictionary for {ListOfSeriesGroup}.
    ListOfSeriesGroupUnique = dict(ListOfSeriesGroup) #ListOfSeriesGroup:
    ListOfSeriesGroupUniqueRev = dict(ListOfSeriesGroupRev)
    
    # Make a compact dictionary\tuple for {ListOfSeriesPairs}.
    outlines = outlines + '------ListOfSeriesPairs---------'+ '\n'
    for SeriesPair in ListOfSeriesPairs:
        outlines = outlines + SeriesPair[0] + ', ' + SeriesPair[1] + '\n';
            
    outlines = outlines + 'Size: ' + str(len(ListOfSeriesPairs)) + '\n\n';
    outlines = outlines + '------ListOfSeriesGroup---------' + '\n'
    
    #for SeriesPair in ListOfSeriesGroup:
    #   outlines = outlines + SeriesPair[0] + ', ' + SeriesPair[1] + '\n';
    for k,v in ListOfSeriesGroupUnique.iteritems():
        outlines = outlines + k + ', \t\t' + v + '\n';
    outlines = outlines + 'Size: ' + str(len(ListOfSeriesGroupUnique)) + '\n\n';
    
    outlines = outlines + '------ListOfSeriesGroupRev---------' + '\n'

    #Calculate total number of the files of each series
    for k,v in ListOfSeriesGroupUniqueRev.iteritems():
        imagefList = []
        #print 'key -> ', v, # '\n'
        for SeriesPair in ListOfSeriesPairs:
            if SeriesPair[1] == k: # v:
                #print SeriesPair[1], '\t\t', v 
                imagefList.append(SeriesPair[0])  
                
        outlines = outlines + k + ', \t\t' + v + '\t\t' + str(len(imagefList)) + '\n';
        
    outlines = outlines + 'Size: ' + str(len(ListOfSeriesGroupUniqueRev)) + '\n\n';
    outlines = outlines + 'StudyInstanceUID: ' + str(iExamUID) + '\n';
    outlines = outlines + '\n\n------ListOfSeriesGroup::image files---------' + '\n'

    #List all files of each series
    for k,v in ListOfSeriesGroupUniqueRev.iteritems():
        imagefList = []     
        for SeriesPair in ListOfSeriesPairs:
            if SeriesPair[1] == k: # v:
                imagefList.append(SeriesPair[0])                
                #outlines = outlines + SeriesPair[0] + '\n';
        outlines = outlines + k + ', \t\t' + v + '\t\t' + str(len(imagefList)) + '\n\n';

    writeSortedPulledFile = open('outcome'+os.sep+'sortedPulledDicomFiles.txt', 'w')    
    try:
        writeSortedPulledFile.writelines(outlines)
    finally:
        writeSortedPulledFile.close()   
    
    #################################################################
    # 3rd-Part: Anonymize/Modify images.                  #
    # (0020,000D),StudyUID  (0020,000e),SeriesUID                   #
    # (0010,0010),PatientName/ID                                    #
    # (0012,0021),"BRCA1F"  (0012,0040),StudyNo                     #
    #################################################################
    print 'Anonymize images at cwd: ' + os.getcwd()
    
    # Make anonymized UID.
    print 'Check out system date/time to form StudyInstUID and SeriesInstUID ' # time.localtime() 
    tt= time.time() # time(). e.g. '1335218455.013'(14), '1335218447.9189999'(18)
    shorttime = '%10.5f' % (tt)         # This only works for Python v2.5. You need change if newer versions.
    SRI_DCM_UID = '1.2.826.0.1.3680043.2.1009.'
    hostIDwidth = len(hostID)    
    shostID = hostID[hostIDwidth-6:hostIDwidth] # Take the last 6 digits
    
    anonyStudyUID = SRI_DCM_UID + shorttime + '.' + hostID + str(AccessionN).strip() ;
    print 'anonyStudyUID->', anonyStudyUID, '\n'
    aPatientID = StudyID + 'CADPat' 
    aPatientName = 'Patient ' + StudyID + 'Anon'

    #For Loop: every Series# with the Exam# in Anonymizing  
    sIndex = 0  
    ClinicTrialNo = StudyID.strip()
    print 'ClinicTrialNo: "' + ClinicTrialNo + '"'
    print 'Begin Modify ....' ;
    for k,v in ListOfSeriesGroupUniqueRev.iteritems():
        sIndex = sIndex + 1 
        imagefList = []
        tt= time.time() 
        shorttime = '%10.7f' % (tt)     
        anonySeriesUID = SRI_DCM_UID + '' + shorttime + '' + shostID + v + '%#02d' % (sIndex)       
        #print 'key -> ', v, '\t', 'anonySeriesUID->', anonySeriesUID, # '\n' '\t\t\t', k    

        for SeriesPair in ListOfSeriesPairs:
            #print SeriesPair
            if SeriesPair[1] == k: # v:
                print SeriesPair[1], '\t\t', v #, '\n' ###[0], '\t\t', k #, '\n'
                imagefList.append(SeriesPair[0])                
                cmd = program_loc+os.sep+'dcmodify -gin -m "(0020,000D)=' + anonyStudyUID + '" -m "(0020,000e)=' + anonySeriesUID + '" \
                -m "(0010,0010)=' + aPatientName + '" -m "(0010,0020)=' + aPatientID +'" \
                -m "(0008, 0090)="Anon" -m "(0008, 1050)="Anon" -m "(0008, 1070)="Anon" -m "(0032, 1032)="Anon" -m "(0033, 1013)="Anon" -m "(0033, 1016)="Anon" -m "(0033, 1019)="Anon" -m "(0033, 101c)="Anon" \
                -i "(0012,0021)=BRCA1F" -i "(0012,0040)=' + ClinicTrialNo + '" ' + SeriesPair[0] + ' > outcome'+os.sep+'dcmodifiedPulledDicomFiles.txt'     
                lines = os.system(cmd)
                
        print '(', len(imagefList), ' images are anonymized.)'
        
    print 'Total Series: ' + str(len(ListOfSeriesGroupUniqueRev)) + '\n';
    print 'cmd -> ' + cmd + '\n'    
    
    ##########################################################################
    # Clean files
    os.chdir(path_rootFolder+os.sep+str(StudyID)+os.sep+str(AccessionN))
    
    bakimagepath = ('*.bak').strip() # (iExamID + '\\*.bak').strip()
    print 'Clean backup files (' + bakimagepath + ') ....' ;
        
    for fl in glob.glob(bakimagepath): 
        #Do what you want with the file
        #print fl
        os.remove(fl)
        
    print 'Backed to cwd: ' + os.getcwd()
            
    
    ##########################################################################
    # 4-Part: Check anonymized Dicomd files resulted from modifing process.  #
    # This is used to compare with pulled Dicom Files.                       #
    # Finallly sort anonnimized files                                                                     #
    ##########################################################################
    print 'Next, to group "anonymized" image files into a hierarchical. ...'
    print 'imagepath: ', imagepath
    
    #########################################
    os.chdir(str(program_loc))
    
    # Group all image files into a number of series for StudyUID/SeriesUID generation.
    cmd = program_loc+os.sep+'dcmdump +f -L +F +P "0020,000e" +P "0020,0011" "' + imagepath + '" > outcome'+os.sep+'anonyPulledDicomFiles.txt'   
    print 'cmd -> ' + cmd
    print 'Begin SortAnonyDicom ....' ;
    lines = os.system(cmd) 
    
    readAnonDicomFile = open('outcome'+os.sep+'anonyPulledDicomFiles.txt', 'r')
    print '---------------------------------------'
    ListOfSeriesGroup    = [] ; # [SeriesNo, SeriesUID] # SeriesNumber
    ListOfSeriesGroupRev = [] ; # [SeriesUID, SeriesNo]     
    ListOfSeriesPairs    = [] ; # [imageFn, SeriesUID]
    #ListOfExamsID = []
    outlines = ""
    nextline = readAnonDicomFile.readline()
    while ( nextline ) : 
        if 'dcmdump' in nextline:
        
            item = nextline; #[0] 
            imageFn = item[item.find(')')+2 : item.find('\n')]      
            
            nextline = readAnonDicomFile.readline() # ( 'SeriesNumber' : #(0020,0011) IS
            item = nextline; #[0] 
            SeriesNo = item[item.find('[')+1:item.find(']')]
            
            nextline =  readAnonDicomFile.readline() # ( 'SeriesInstanceUID' :  #(0020,000e) SH
            item = nextline; #[0]
            SeriesUID = item[item.find('[')+1:item.find(']')]
            
            ListOfSeriesGroup.append([SeriesNo, SeriesUID])
            ListOfSeriesPairs.append([imageFn, SeriesUID])
            
            nextline = readAnonDicomFile.readline()
        else:
            nextline = readAnonDicomFile.readline()
    readAnonDicomFile.close()
    
    #
    # Make a compact dictionary for {ListOfSeriesGroup}.
    ListOfSeriesGroupUnique = dict(ListOfSeriesGroup) #ListOfSeriesGroup:
    ListOfSeriesGroupUniqueRev = dict(ListOfSeriesGroupRev)
                
    outlines = outlines + '------ListOfSeriesPairs---------'+ '\n'
    
    for SeriesPair in ListOfSeriesPairs:
        outlines = outlines + SeriesPair[0] + ', ' + SeriesPair[1] + '\n';

    outlines = outlines + 'Size: ' + str(len(ListOfSeriesPairs)) + '\n\n';
    outlines = outlines + '------ListOfSeriesGroup---------' + '\n'
    
    for k,v in ListOfSeriesGroupUnique.iteritems():
        outlines = outlines + k + ', \t\t' + v + '\n';
    outlines = outlines + 'Size: ' + str(len(ListOfSeriesGroupUnique)) + '\n\n';

    outlines = outlines + '------ListOfSeriesGroupRev---------' + '\n'

    #Calculate total number of the files of each series
    for k,v in ListOfSeriesGroupUniqueRev.iteritems():
        imagefList = []
        print 'key -> ', v, '\n'
        for SeriesPair in ListOfSeriesPairs:
            if SeriesPair[1] == k: # v:
                imagefList.append(SeriesPair[0])        
                
        print '(', len(imagefList), ' images.)\n'
        outlines = outlines + k + ', \t\t' + v + '\t\t' + str(len(imagefList)) + '\n';
    outlines = outlines + 'Size: ' + str(len(ListOfSeriesGroupUniqueRev)) + '\n\n';
    
    ### Extra action to extract StudyInstUID.
    anyAnonDicomFile = (ListOfSeriesPairs[0])[0] #Take one file to extract StudyInstUID
    cmd = program_loc+os.sep+'dcmdump +f -L +F +P "0020,000d" "' + anyAnonDicomFile.strip() + '" > outcome'+os.sep+'anonyPulledDicomStudyUID.txt'    
    print 'cmd -> ' + cmd
    print 'Begin SortDicom ....' ;
    lines = os.system(cmd) 
    
    readAnonDicomStudyUID = open('outcome'+os.sep+'anonyPulledDicomStudyUID.txt', 'r')
    nextline =  readAnonDicomStudyUID.readline()
    item =  readAnonDicomStudyUID.readline() # ( 'StudyInstanceUID' :   #(0020,000d) UI
    
    #   print 'nextline: ', nextline, '; item: ', item
    AnonStudyUID = item[item.find('[')+1:item.find(']')]
    print 'AnonStudyUID => ' + AnonStudyUID 
    readAnonDicomStudyUID.close()
    ###
    
    
    outlines = outlines + 'AnonStudyInstanceUID: ' + str(AnonStudyUID) + '\n'; #iExamUID
    outlines = outlines + '\n\n------ListOfSeriesGroup::image files---------' + '\n'

    #List all files of each series
    for k,v in ListOfSeriesGroupUniqueRev.iteritems():
        imagefList = []
        #print 'key -> ', v, '\n\n'
        for SeriesPair in ListOfSeriesPairs:
            if SeriesPair[1] == k: # v:
                imagefList.append(SeriesPair[0])                
                outlines = outlines + SeriesPair[0] + '\n';
        #print len(imagefList), '\n\n'
        outlines = outlines + k + ', \t\t' + v + '\t\t' + str(len(imagefList)) + '\n\n';
    
    writeSortedAnonFile = open('outcome'+os.sep+'anonyPulledsortedAnonyDicomFiles.txt', 'w')   
    try:
        writeSortedAnonFile.writelines(outlines)
        # Do things with fileh here
    finally:
        writeSortedAnonFile.close() 
            
    
    ###################################################################
    # 5-Part: Finally Pushed annonimized files to destination      #
    # This is used to compare with pulled Dicom Files.                #
    # Finallly sort anonnimized files                              #
    ###################################################################
    print " imagepath -> ", imagepath
    cmd = program_loc+os.sep+'storescu -v -aet ' + my_aet + ' -aec ' + remote_aet + ' ' + remote_IP + \
        ' ' + remote_port + ' "' + imagepath + '" > outcome'+os.sep+'push_results.txt' # ' C:\\BMRIWorker\\Temp\\2211321SHSC\\*.dcm 
    
    print "Push exam to destination (no exam found at destination). " 
    print "cmd -> " + cmd
    print 'Now Begin push ....' ;
    p1 = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p1.wait()
    
    print "This Exam is on archived succesfully."
    
    #########################Loop for iExamPair ####################################
    
    #Cleanup the tmp directory.
    try:
        if os.path.isdir(StudyID):
            shutil.rmtree(StudyID)    #os.rmdir(StudyNo)    #remove    # removedirs
    except ValueError:
        print "Deleting a Directory is problematic."    
            
    return


########################### START ####################################
if __name__ == '__main__':
    # Get Root folder ( the directory of the script being run)
    path_rootFolder = os.path.dirname(os.path.abspath(__file__))
    print path_rootFolder
    
    if not os.path.exists('outcome'):
        os.makedirs('outcome')
    
    if not os.path.exists('querydata'):
        os.makedirs('querydata')
        
    if not os.path.exists('querydata_Database'):
        os.makedirs('querydata_Database')
    
    if not os.path.exists('checkdata'):
        os.makedirs('checkdata')    
            
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
                check_pacs(path_rootFolder, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN)
                    
                # 2) Annonimize StudyId/AccessionN pair from pacs
                pull_pacs(path_rootFolder, remote_aet, remote_port, remote_IP, local_port, PatientID, StudyID, AccessionN)
                                
                # 3) Warite to Series/Level table in biomatrix 
                #exam_loc = program_loc+os.sep+str(StudyID)+os.sep+str(AccessionN)
                update_table(PatientID, StudyID, AccessionN) 
                            
        finally:
            file_ids.close()
    

