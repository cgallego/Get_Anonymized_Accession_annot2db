# -*- coding: utf-8 -*-
"""
SQL interaction part of the thumbnailer: schema for the metadata.
"""

import sqlalchemy.orm
al = sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
def connect(con):
    """Establish connection using supplied connection string."""
    global Session,s,engine
    engine = al.create_engine(con)
    engine.connect()
    Base.metadata.bind = engine
    Base.metadata.create_all(engine) 
    Session = al.orm.sessionmaker(bind=engine)
    s = Session()

class Meta(Base):
    """Object-entity record for each entry. Properties should be set
    by calling .from_dicom()"""
    __tablename__ = 'meta'
    FORMS = {0:'CALIPER', 1:'LINEARROW', 2:'ELLIPSE'}

    #Basic descriptors
    id = al.Column(al.Integer, primary_key=True)
    accession = al.Column(al.Integer)
    orig = al.Column(al.String(100))
    form = al.Column(al.Integer) # one of FORMS
    series = al.Column(al.Integer)
    
    #Pixel coords
    x1 = al.Column(al.Integer)
    y1 = al.Column(al.Integer)
    x2 = al.Column(al.Integer)
    y2 = al.Column(al.Integer)
    slice = al.Column(al.Integer)
    
    #DICOM coords, annotation centre
    X = al.Column(al.Float)
    Y = al.Column(al.Float)
    Z = al.Column(al.Float)

    #Links
    pt_exam_finding = al.Column(al.Integer)   # link to BioMatrix 
    im_file = al.Column(al.String(100))
    URL = al.Column(al.String(100))

    def __repr__(self):
        return "Annotation Metadata %i"%(self.id or -1)    
        
    def fields(self):
        "The set of field names"
        return self.__table__.c.keys()
        
    def fields_csv(self):
        "The field names as approrpiate for the first line of a CSV"
        return ",".join(self.fields())
    
    def to_csv(self):
        "The record data as comma-separated"
        return ",".join(str(self.__getattribute__(k)) for k in self.fields())
    
    def set_form(self, string):
        "Given an annotation string identifier, pick numerical FORM"
        for k in self.FORMS:
            if string==self.FORMS[k]:
                self.form = k
                return
        raise IndexError("Annotation type not understood")

    def from_dicom(self, dicomfile, ann, pars):
        """
        Update object from supplied information
        """
        self.accession = int_or_not( dicomfile, (0x08, 0x50))
        self.series = int( dicomfile.SeriesNumber )
        self.orig = dicomfile.get((0x029, 0x1300)).value
        form = ann[0]
        self.set_form( form )
        self.x1,self.y1,self.x2,self.y2 = ann[2:6]
        self.slice = int(dicomfile.InstanceNumber or "-1")
        
        if form=='CALIPER':
            self.Z,self.Y,self.X = (ann[-2] + ann[-1])/2
        elif form=='LINEARROW':
            self.Z,self.Y,self.X = ann[-1]
        else: 
            self.Z,self.Y,self.X = ann[-2]
            
        self.im_file = pars['im_file']
        self.URL = pars['URL']
        
    def string_all(self):
        return "".join(["%s: %s\n"%(k,self.__getattribute__(k)) for k
                    in self.fields()])
        
def int_or_not(dicomfile, tag):
    try:
        val = dicomfile.get(tag).value
        return int(val)
    except:
        return -1

def is_duplicate(meta):
    "See whether a record matching this one already exists in the database"
    records = s.query(Meta).all()
    fields = ['accession','series','orig','slice']
    for rec in records:
        if min(rec.__getattribute__(f)==meta.__getattribute__(f) for f in fields) > 0:
            return rec
    return False
        
def all_acc(acc):
    """Output all records matching accession. Presumes session is 
    already set up.
    
    acc: input accession string."""
    acc2 = int("".join([a for a in acc if a.isdigit()]))
    recs = s.query(Meta).filter(Meta.accession==acc2)
    for rec in recs:
        print rec.string_all()
        print
    if len(recs)==0:
        print "No records found"