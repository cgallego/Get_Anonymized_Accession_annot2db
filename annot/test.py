# -*- coding: utf-8 -*-
"""
Test the annotation scanner/thumbnailer.
"""

test_set = "Z:/Cristina/Pipeline4Archive/Get_Anonymized_Accession_annot2db/querydata_Database/4809893" # input DICOMS
test_dir = "Z:/Cristina/Pipeline4Archive/Get_Anonymized_Accession_annot2db/annot/annot_imgs" # output images
test_URL = "Z:/Cristina/Pipeline4Archive/Get_Anonymized_Accession_annot2db/annot/annot_imgs" # fake URL root
test_con = 'sqlite+pysqlite:///Z:/Cristina/Pipeline4Archive/Get_Anonymized_Accession_annot2db/annot/localannot.db3' # DB file

test_pars = pars = {'directory':test_set, 'im_path':test_dir, 'URLroot':test_URL, 
                    'logfile':'Z:/Cristina/Pipeline4Archive/Get_Anonymized_Accession_annot2db/annot/annot_log', 
                    'sql':test_con,
                    'logmode':'a',
                    'clobber':True,
                    'dry_run':False, 'log':None}
                    
                    
from annot import main

main.scan_directory(test_pars) 