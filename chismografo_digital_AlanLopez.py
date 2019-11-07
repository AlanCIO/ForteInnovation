# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 13:19:25 2019

@author: ALopez

ForteInnovation Test
"""
# Needed modules
import pymongo
from datetime import datetime

# DataBase
client = pymongo.MongoClient("mongodb://localhost:27017/")

# Future work: A wrap for the database can later be code;
# could improve efficiency for different data sources
db = client["chismografo_database"]
usersCollection = db["user"]
questionsCollection = db["question"]
answersCollection = db["answer"]

class interface:
    def __init__(self):
        self.activeChismografo = chismografo()
        # Set Chismografo sample
        self.activeChismografo.setChismografoSample()
        self.users = []
        self.activeUserId = None
        
    def execute(self):
        options = {"1": self.__signUp,\
                   "2": self.__signIn}
        op = input("Opciones:\n\t1 Regístrate \n\t2 Ingresa\n")
        action = options.get(op)
        if action:
            isValidated = action()
            # Menu access only for validated sign-Up(In)
            if isValidated:
                self.__displayMenu()
        else:
            print("{0} no es una opción válida".format(op))

    def setNewQuestion(self,description):
        self.activeChismografo.newQuestion(description)

    def __signUp(self):
        print("Registro")
        fullName = input("Ingresa tu nombre *completo*:\n")
        email    = input("Ingresa tu correo electrónico:\n")
        userName = input("Ingresa tu nombre de usuario:\n")
        password = input("Ingresa tu contraseña:\n")
        Id = len(self.users)+1
        newUser = user(Id,fullName,email,userName,\
                       self.__encrypt(password))
        
        newUser.joinChismografo(self.activeChismografo)
        self.activeUserId = newUser.Id
        self.users.append(newUser)
        
        # Validated Sign-Up 
        isValidated = True
        
        return isValidated
                
    def __signIn(self):
        print("Ingresa\n")
        userName = input("Ingresa tu nombre de usuario:\n")
        password = input("Ingresa tu contraseña:\n")
        
        user = self.__searchUserInDB(userName)
    
        if user == None:
            print("Usuario o contraseña incorrecto\n")
            # Invalidated Sign-In
            isValidated = False
        else:
            if password == self.__decrypt(user["password"]):
                print("Credenciales válidas. Estás dentro\n")
                self.activeUserId = user["_id"]
                # Validated Sign-In
                isValidated = True
            else:
                print("Usuario o contraseña incorrecto\n")
                # Invalidated Sign-In
                isValidated = False                
        return isValidated

    def __displayMenu(self):        
        # Set active user of the current session
        userId = self.activeUserId
        
        # If the user has missing answers, she'll be
        # requested to answer each question
        # (there cannot be unanswered questions)
        while(not self.__isAllAnswered(userId) ):
            self.__editAnswers()
            
        # Users with all answers can access
        # the Chismografo menu 
        print("Tienes *todas* las respuestas; puedes ver el menú")        
        while True:
            options = {"1": self.__editAnswers,\
                       "2": self.__deleteUser,\
                       "3": self.__showAnswers,
                       "4": self.__sendEmail,}
            op = input("Opciones:\n\t1 Editar respuestas \n\t2 Eliminar\n\t3 Listado\n\t4 Enviar\nCualquier otra\tsalir\n")
            action = options.get(op)
            if action:
                action()
                # When user delete herself from the
                # chismografo, she cannot longer access
                # the chismografo menu
                if action == self.__deleteUser:
                    break
            else:
                # Any other case allow user to exit
                # chismografo menu
                print("Saliendo")
                break
       
    def __editAnswers(self):
        userId = self.activeUserId
        user = self.users[userId-1] #lists start at 0. Id keys at 1
        
        print("Estás listo para responder preguntas\n")
        questions = self.activeChismografo.getQuestions()
        for question in questions:
            print(question["description"], end=" ")
            answer = self.activeChismografo.getAnswer(question, userId)
            # An answer has been previously provided by active user
            if answer != None:
                print("("+answer["description"]+")")
                description = input("Nueva respuesta (enter to pass):\n")
                if description !="":
                    user.answerQuestion(userId,question["_id"],description, isFirstAnswer=False)
            # Answer has *not* been previously provided by active user
            else:
                description = input("No has respondido.\n Ingresa tu respuesta (enter to pass):\n")
                if description !="":
                    user.answerQuestion(userId,question["_id"],description, isFirstAnswer=True)
    
    def __deleteUser(self):
        print("Eliminar\n")
        userId = self.activeUserId
        db.user.delete_one({"_id": userId})
        db.answer.delete_many({"user": userId})
        print("Usuario eliminado")
    
    def __showAnswers(self):
        print("Listado\n")
        userId = self.activeUserId        
        user = self.users[userId-1]#lists start at 0. Id keys at 1
    
        # Print chismografo header
        questions = self.activeChismografo.getQuestions()
        print("username|",end="\t")
        for question in questions:
            print(question["description"], end="|\t")
        print("\n",user.userName,end="|\t")
        
        # Print active-user answers
        questions = self.activeChismografo.getQuestions()
        for question in questions:
            answer = self.activeChismografo.getAnswer(question, userId)
            if answer != None:
                    print(answer["description"], end="|\t")
            else:
                print("|",end="\t")
            
    def __sendEmail(self):
        mailRecipient = input("Ingresa el correo:\n")
        print("Enviando respuestas a " + mailRecipient)

    # Simulate en(de)cryption with an(a) en(de)coding.
    # Methods can later be modified to perform real
    # secure en(de)cryption
    def __encrypt(self,password):
        return password.encode('utf-16')
    def __decrypt(self,encrypted_password):
        return encrypted_password.decode('utf-16')

    def __isAllAnswered(self,userId):
        #numAnswers = db.answer.count_documents({"user":userId},{"description":"true"})
        numAnswers = db.answer.find({"user":userId},{"description":"true"}).count()
        totalQuestions = db.question.count_documents({})
        if numAnswers < totalQuestions:
            return False
        else:
            return True 
               
    def __searchUserInDB(self, userName):
        return db.user.find_one({"username":userName})
            
    def __del__(self):
        usersCollection.drop()
        questionsCollection.drop()
        answersCollection.drop()
        self.users.clear()

class user:
    def __init__(self, Id, fullName, email, userName,\
                 encriptedPassword):
        self.Id = Id
        self.fullName = fullName
        self.email = email
        self.userName = userName
        self.encriptedPassword = encriptedPassword
        
        self.joinedChismografo = None
   
    def joinChismografo(self, chismografo):
        self.joinedChismografo = chismografo
        
        name_string = self.fullName.split()
        if len(name_string) == 3:
            name = name_string[0]
            firstLastName = name_string[1]
            secondLastName = name_string[2]
        elif len(name_string) == 0:
            name = ""
            firstLastName = ""
            secondLastName = ""
        else:
            name = name_string[0]
            firstLastName = ""
            secondLastName = ""
            
        newUser= {"_id": self.Id,\
                  "username": self.userName,\
                  "fullName": 
                      {"name": name,\
                       "firstLastName": firstLastName,\
                       "secondLastName": secondLastName,\
                      },\
                  "email": self.email,\
                  "password": (self.encriptedPassword)}
        usersCollection.insert_one(newUser)
        self.Id = newUser["_id"]
        
    def answerQuestion(self,userId, questionId, description, isFirstAnswer):
        if isFirstAnswer:
            self.joinedChismografo.totalAnswersNum +=1
            absoluteAnswerId = self.joinedChismografo.totalAnswersNum
            answer = {"_id": absoluteAnswerId,\
                      "user":userId,\
                      "question": questionId,\
                      "description": description,\
                      "date": datetime.now().strftime("%m/%d/%Y")}
            answersCollection.insert_one(answer)        
        else:
            query = {"user": userId, "question": questionId}
            newAnswer = { "$set": {"description": description,\
                                   "date": datetime.now().strftime("%m/%d/%Y")}}        
            answersCollection.update_one(query, newAnswer)
                   
class chismografo:
    def __init__(self):
        self.totalAnswersNum = 0
    
    def setChismografoSample(self):
        self.newQuestion("¿Cuántos años tienes?")
        self.newQuestion("¿Cuál es el nombre de tu mascota?")
        self.newQuestion("¿Dónde trabajas?")

    def newQuestion(self,description):
        question = {"_id": db.question.count_documents({}) + 1,\
                    "description": description}
        questionsCollection.insert_one(question)
        
    def getQuestions(self):
        return db.question.find({})
    
    def getAnswer(self,question, userId):
        return db.answer.find_one({"question": question["_id"],"user": userId})

# ----------- Execute interface --------------
interfaz = interface()
while True:
    interfaz.execute()
    stop = input("Ingresa c para terminar el ejemplo:\t")
    if stop == "c":
        del(interfaz)
        client.close()
        print("Ejemplo terminado")
        break
