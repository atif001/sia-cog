from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.exc import NoResultFound

from projectmodels import *
import simplejson as json
from datetime import datetime
import uuid
from passlib.hash import pbkdf2_sha256

engine = create_engine(DBPath())
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = scoped_session(DBSession)

def GetService(srvname, srvtype):
    result = None
    try:
        result = session.query(Service).filter(Service.servicetype == srvtype).filter(Service.servicename == srvname).one()
    except NoResultFound as e:
        result = None

    return result

def ValidateServiceExists(srvname, srvtype):
    s = GetService(srvname, srvtype)
    if s is None:
        raise Exception("Service does not exists")

def GetServices(srvtype):
    result = None
    try:
        result = session.query(Service).filter(Service.servicetype == srvtype).all()
    except NoResultFound as e:
        result = None

    return result

def GetPipeline(srvname, srvtype):
    result = None
    try:
        result = session.query(Pipeline).filter(Pipeline.servicetype == srvtype).filter(Pipeline.servicename == srvname).one()
    except NoResultFound as e:
        result = None

    return result

def GetDeepModel(srvname, srvtype, modelname):
    result = None
    try:
        result = session.query(DeepModel).filter(DeepModel.servicetype == srvtype).filter(DeepModel.servicename == srvname).filter(DeepModel.modelname == modelname).one()
    except NoResultFound as e:
        result = None

    return result

def GetDeepModels(srvname, srvtype):
    result = None
    try:
        result = session.query(DeepModel).filter(Service.servicetype == srvtype).filter(Service.servicename == srvname).all()
    except NoResultFound as e:
        result = None

    return result

def UpsertService(srvname, srvtype, srvdata):
    try:
        srv = GetService(srvname, srvtype)
        if srv is None:
            srv = Service(servicename=srvname, servicetype=srvtype, servicedata=json.dumps(srvdata), createdon=datetime.utcnow(), modifiedon=datetime.utcnow())
            session.add(srv)
        else:
            srv.servicedata = json.dumps(srvdata)
            srv.modifiedon = datetime.utcnow()

        session.commit()
    except:
        session.rollback()
        raise

def UpsertPipeline(srvname, srvtype, pipelinedata, pipelineflow=None):
    try:
        pd = GetPipeline(srvname, srvtype)
        if pd is None:
            pd = Pipeline(servicename=srvname, servicetype=srvtype, pipelinedata=json.dumps(pipelinedata), pipelineflow=pipelineflow, createdon=datetime.utcnow(), modifiedon=datetime.utcnow())
            session.add(pd)
        else:
            pd.pipelinedata = json.dumps(pipelinedata)
            pd.modifiedon = datetime.utcnow()
        session.commit()
    except:
        session.rollback()
        raise

def UpdatePipelineFlow(srvname, srvtype, pipelineflow):
    try:
        pd = GetPipeline(srvname, srvtype)
        if not pd is None:
            pd.pipelineflow = json.dumps(pipelineflow)
            pd.modifiedon = datetime.utcnow()
            session.commit()
    except:
        session.rollback()
        raise

def UpdateModelFlow(srvname, srvtype, modelname, modelflow):
    try:
        dm = GetDeepModel(srvname, srvtype, modelname)
        if not dm is None:
            dm.modelflow = json.dumps(modelflow)
            dm.modifiedon = datetime.utcnow()
            session.commit()
    except:
        session.rollback()
        raise

def UpsertDeepModels(srvname, srvtype, modelname, modeldata, modelflow=None):
    try:
        model = GetDeepModel(srvname, srvtype, modelname)
        if model is None:
            model = DeepModel(servicename=srvname, servicetype=srvtype, modelname=modelname, modeldata=json.dumps(modeldata), modelflow=modelflow, createdon=datetime.utcnow(), modifiedon=datetime.utcnow())
            session.add(model)
        else:
            model.modeldata = json.dumps(modeldata)
            model.modifiedon = datetime.utcnow()
        session.commit()
    except:
        session.rollback()
        raise

def DeleteService(srvname, srvtype):
    try:
        srv = GetService(srvname, srvtype)
        session.delete(srv)
        session.commit()
    except:
        session.rollback()
        raise

def DeletePipeline(srvname, srvtype):
    try:
        pd = GetPipeline(srvname, srvtype)
        session.delete(pd)
        session.commit()
    except:
        raise

def GetJob(id):
    result = None
    try:
        result = session.query(TrainingJob).filter(TrainingJob.id == id).one()
    except NoResultFound as e:
        result = None

    return result

def GetJobs(srvname, srvtype):
    result = session.query(TrainingJob).filter(TrainingJob.servicetype == srvtype).filter(TrainingJob.servicename == srvname).all()
    return result

def StartJob(srvname, srvtype, totalepoch):
    try:
        id = str(uuid.uuid4())
        job = TrainingJob(id=id, servicename=srvname, servicetype=srvtype, start=datetime.utcnow(), status="Started", createdon=datetime.utcnow(), totalepoch=totalepoch)
        session.add(job)
        session.commit()
    except:
        session.rollback()
        raise
    return id

def EndJob(id, status, message, result=None):
    try:
        job = GetJob(id)
        job.end = datetime.utcnow()
        job.status = status
        job.message = message
        job.result = result
        session.commit()
    except:
        session.rollback()
        raise

def UpdateModelHistory(id, history):
    try:
        job = GetJob(id)
        job.modelhistory = history
        session.commit()
    except:
        raise

def ClearCurrentTraining(id):
    try:
        session.query(CurrentTraining).filter(CurrentTraining.id == id).delete()
        session.commit()
    except:
        session.rollback()
        raise

def LogCurrentTraining(id, epoch, loss):
    try:
        log = CurrentTraining(id=id, epoch=epoch, loss=loss)
        session.add(log)
        session.commit()
    except:
        session.rollback()
        raise

def GetCurrentTraining(id):
    return session.query(CurrentTraining).filter(CurrentTraining.id == id).order_by(CurrentTraining.epoch).all()

def GetUserInfo(username):
    result = None
    try:
        result = session.query(LoginUser).filter(LoginUser.username == username).one()
    except NoResultFound as e:
        result = None
    return result

def CreateUser(username, password, name, email):
    try:
        passhash = pbkdf2_sha256.hash(password)
        user = LoginUser(username=username, password=passhash, name=name, email=email, createdon=datetime.utcnow(), modifiedon=datetime.utcnow())
        session.add(user)
        session.commit()
    except:
        session.rollback()
        raise

def UpdateUser(username, name, email):
    try:
        user = GetUserInfo(username)
        if user is None:
            raise Exception("User not found")
        user.name = name
        user.email = email
        session.commit()
    except:
        session.rollback()
        raise

def UpdateUserPassword(username, password):
    try:
        user = GetUserInfo(username)
        if user is None:
            raise Exception("User not found")
        user.password = pbkdf2_sha256.hash(password)
        session.commit()
    except:
        session.rollback()
        raise

def ValidateUser(username, password):
    result = False
    try:
        user = GetUserInfo(username)
        if user is None:
            raise Exception("User not found")

        result = pbkdf2_sha256.verify(password, user.password)
    except:
        raise

    return result