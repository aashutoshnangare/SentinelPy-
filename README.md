# SentinelPy-
System Health Monitor with Periodic Reporting
- Silent background agent that monitors CPU, RAM,
  Disk, Network & 100+ processes simultaneously
- Auto-generates forensic-style log reports and 
  dispatches real-time email intelligence reports
  surveillance.py
-Project Structure

│
├── main()                    # Entry point, CLI argument handling
├── CreateLog(FolderName)     # Generates a full system log file
├── ProcessScan()             # Scans all running processes
├── GetTop10Processes()       # Returns top 10 by memory usage
├── GetEmailSummary()         # Builds a plain-text summary for email body
├── Marvellous_send_mail(...) # Sends email with log as attachment
└── SendEmailPerodically(...) # Combines log creation + email sending
