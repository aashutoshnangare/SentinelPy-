import psutil
import sys
import os
import time
import schedule
import smtplib
from email.message import EmailMessage


def CreateLog(FolderName):
    Border = "-"*57
    Ret = False

    Ret = os.path.exists(FolderName)

    if(Ret == True):
        Ret = os.path.isdir(FolderName)
        if(Ret == False):
            print("Unable To Create Folder")
            return
        
    else:
        os.mkdir(FolderName)
        print("Directory For Log Files Gets Created Sucessfully")

    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    
    FileName = os.path.join(FolderName,"System_Surviellance_%s.log"%timestamp)
    print("Log File Gets Created With Name",FileName)

    fobj = open(FileName,"w")
    fobj.write(Border+"\n")
    fobj.write("--------------Platform Surveillance System---------------"+"\n")
    fobj.write("Log created at : "+time.ctime()+"\n")
    fobj.write(Border+"\n\n")

    fobj.write("-------------------System Report-------------------------\n")

    #print("CPU Usage : ",psutil.cpu_percent())
    fobj.write("CPU Usage : %s %%\n"%psutil.cpu_percent())
    fobj.write(Border+"\n")


    mem = psutil.virtual_memory()
    #print("RAM Usage : ",mem.percent)
    fobj.write("RAM Usage : %s %%\n"%mem.percent)
    fobj.write(Border+"\n")

    fobj.write("\nDisk Usage Report\n")
    fobj.write(Border+"\n")

    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            #print(f"{part.mountpoint} used {usage.percent}%%")
            fobj.write("%s -> %s %% used\n"%(part.mountpoint,usage.percent))
        except:
            pass
    fobj.write(Border+"\n")
    
    net = psutil.net_io_counters()
    fobj.write("\nNetwork Usage Report\n")
    fobj.write("Sent : %.2f MB\n"%(net.bytes_sent/(1024 *1024)))
    fobj.write("Recv : %.2f MB\n"%(net.bytes_recv/(1024 *1024)))
    fobj.write(Border+"\n")

    Data = ProcessScan()
    
    for info in Data:
        fobj.write("PID : %s\n" %info.get("pid"))
        fobj.write("Name : %s\n" %info.get("name"))
        fobj.write("UserName : %s\n" %info.get("username"))
        fobj.write("Number of threads : %s\n"%info.get("thread"))
        fobj.write("Status : %s\n" %info.get("status"))
        fobj.write("Start Time : %s\n" %info.get("create_time"))
        fobj.write("CPU %% : %2f\n" %info.get("cpu_percent"))
        fobj.write("Memory %% : %2f\n" %info.get("memory_percent"))
        fobj.write("Open Files %% : %s\n" %info.get("open_files")) 
        fobj.write("RSS (Actual RAM) : %.2f MB\n" % info.get("rss_mb", 0))
        fobj.write("VMS (Virtual Memory): %.2f MB\n" % info.get("vms_mb", 0))
        fobj.write(Border+"\n")

    fobj.write("\n------- Top 10 Memory Consuming Processes -------\n")
    top10 = GetTop10Processes()
    for i in range(len(top10)):
        proc = top10[i]
        rank = i + 1
        fobj.write(f"Rank : {rank} | Pid : {proc.get("pid")}\n")
        fobj.write("  RSS : %.2f MB | VMS : %.2f MB | Mem%%: %.2f%%\n" % (proc.get("rss_mb", 0), proc.get("vms_mb", 0), proc.get("memory_percent", 0)))

    fobj.write(Border+"\n")
        
    fobj.write(Border+"\n")
    fobj.write("---------------------End Of Log File---------------------"+"\n")
    fobj.write(Border+"\n")
    fobj.close()
    return FileName

def ProcessScan():
    listprocesses = []

    #Warm up for CPU percent
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent()
        except:
            pass

    time.sleep(0.2)

    for proc in psutil.process_iter():
        try:
            info = proc.as_dict(attrs=["pid","name","username","status","create_time"])
            #Convert Createtime
            try:
                info["create_time"] = time.strftime("%Y-%m-%d %H:%M:S",time.localtime(info["create_time"]))
            
            except:
                info["create_time"] = "NA"

            try:
                open_files_list = proc.open_files()
                open_file_count = len(open_files_list)

            except(psutil.AccessDenied):
                open_file_count = "Access Denied"

            except(psutil.NoSuchProcess):
                open_file_count = "Process Ended"

            except(psutil.ZombieProcess):
                open_file_count = "NA"

            info["open_files"] = open_file_count
            info["cpu_percent"] = proc.cpu_percent(None)
            info["memory_percent"] = proc.memory_percent()
            info["thread"] = proc.num_threads()
            mem_info = proc.memory_info()
            info["rss_mb"] =  mem_info.rss / (1024*1024)
            info["vms_mb"] = mem_info.vms / (1024*1024)

            listprocesses.append(info)
        
        except(psutil.NoSuchProcess,psutil.AccessDenied,psutil.ZombieProcess):
            pass

    return listprocesses

def GetTop10Processes():
    Data = ProcessScan()

    sorted_Data = sorted(Data, key=lambda x : x.get("memory_percent",0) ,reverse=True)
    return sorted_Data[:10]

def GetEmailSummary():
    Data = ProcessScan()

    total = len(Data)

    sorted_cpu = sorted(Data , key= lambda x : x.get("cpu_percent",0) , reverse=True)
    top_cpu = sorted_cpu[0]

    sorted_mem = sorted(Data , key= lambda x : x.get("memory_percent",0) , reverse=True)
    top_mem =  sorted_mem[0]

    sorted_thread = sorted(Data , key= lambda x : x.get("thread",0) , reverse=True)
    top_thread = sorted_thread[0]

    valid = []
    for p in Data:
        if isinstance(p.get("open_files") , int):  # filters out Access Denied files
            valid.append(p)

    sorted_files = sorted(valid, key = lambda x : x.get("open_files",0), reverse=True)
    top_openfiles = sorted_files[0] if valid else None

    summary = "System Summary\n"
    summary = summary + "Total Processes : " + str(total) + "\n"
    summary = summary + "Top CPU    : " + str(top_cpu.get("name")) + " -> " + str(top_cpu.get("cpu_percent")) + "%\n"
    summary = summary + "Top Memory : " + str(top_mem.get("name")) + " -> " + str(top_mem.get("memory_percent")) + "%\n"
    summary = summary + "Top Thread : " + str(top_thread.get("name")) + " -> " + str(top_thread.get("thread")) + " threads\n"
    if top_openfiles:
        summary = summary + "Top Files  : " + str(top_openfiles.get("name")) + " -> " + str(top_openfiles.get("open_files")) + " files\n"

    return summary
        
def Marvellous_send_mail(sender, app_password, receiver, subject, body ,attachment_path):
    print(" Mail Sent Successfully")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.set_content(body)

    Efobj = open(attachment_path ,"rb")
    file_data = Efobj.read()
    Efobj.close

    msg.add_attachment(file_data, maintype = "application" , subtype = "octet-stream" , filename = os.path.basename(attachment_path) )

    smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp.login(sender, app_password)
    smtp.send_message(msg)
    smtp.quit()

def SendEmailPerodically(Foldername,receiver):
    log_file = CreateLog(Foldername)
    summary = GetEmailSummary()
    sender_email = "tantriknijja@gmail.com"
    app_password = "fihifqvzuzhboezd"
    subject = "System Report - " + time.ctime()
    
    Marvellous_send_mail(sender_email,app_password,receiver,subject,summary,log_file )

def main():

    Border = "-"*57
    print(Border)
    print("------------- Platform Surveillance System---------------")
    print(Border)

    if (len(sys.argv) == 2):
        if(sys.argv[1] == "--h" or sys.argv[1]=="--H"):
            print("This script is use to : ")
            print("1 : Create Automatic Logs")
            print("2 : Executes Periodically")
            print("3 : Send mail with log")
            print("4 : Store Information about Process")
            print("5 : Store Information about CPU")
            print("6 : Store Information about RAM usage")
            print("7 : Store Information about Secondary Storage")

        elif(sys.argv[1] == "--u" or sys.argv[1]=="--U"):
            print("Use The Automation Script As")
            print("ScriptName.py TimeInterval DirectoryName")
            print("Time Interval : The Time in minuted for periodic scheduling ")
            print("Directory Name : Name of Directory to create auto log")

        else:
            print("Unable to proceed as there no such option")
            print("Please use --h or --u to get more details")

    elif(len(sys.argv) == 3):

        #Apply THe Schduler
        schedule.every(int(sys.argv[1])).minutes.do(CreateLog,sys.argv[2])

        print("Platform Surviellance System Started Sucessfully")
        print("Directory Created With Name : ",sys.argv[2])
        print("Time Interval In Minutes :",sys.argv[1])
        print("Press Ctrl + C To Stop The Execution")

    elif(len(sys.argv) == 4):
        
        schedule.every(int(sys.argv[1])).minutes.do(SendEmailPerodically,sys.argv[2],sys.argv[3])
        print("Email Reporting Started")
        print("Directory : ", sys.argv[2])
        print("Receiver  : ", sys.argv[3])
        print("Interval  : ", sys.argv[1], "minutes")
        print("Press Ctrl+C To Stop")

        #wait till abort
        while True:
            schedule.run_pending()
            time.sleep(1)

    else:
        print("Inavlid Number of Command Line Arguments")
        print("Unable to proceed as there no such option")
        print("Please use --h or --u to get more details")

    print(Border)
    print("-------------Thank You For Using Our Script--------------")
    print(Border)

if __name__ == "__main__":
    main()