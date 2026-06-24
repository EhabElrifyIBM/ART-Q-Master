I want an organised tool to calcualate the reach rate of each channel (SMS - Email - Phone Calls) this will calcualated in process by comparing some sheets, sheets mapping is as follows:

Sheet 1, PA Cases sheet in Active Cases PA Workbook:
    PA Cases sheet columns mapping:
    Case 
    Customer Name
    Company Name	
    DND (Do Not Disturb)	
    Email	
    Phone Number	
    Work Order Type	
    Incoming Channel	
    Last Status Change	
    Country	
    State/Province	
    Local Time	
    Action 1	
    Action 2	
    Action 3	
    Final Action	
    Assigned To	
    Status	
    Unnamed: 18	
    Case	
    Problem Description	
    Case Status Updated	
    Case Reason	
    Work Order ID	
    Work Order Status	
    Order Type	
    Work Order Priority	
    Product ID (MTM)	
    Machine Type	
    Product Description	
    Serial Number	
    Created On	
    Survey Preference	
    Survey Fatigue	
    No survey reason	
    Program	
    Repeat Frequency	
    Repeat Repair	
    Closing Code	
    Reported Symptom	
    Case Status	
    Completion Date

Sheet 2, SMS View:
    Column Mapping:
    SMS Text	
    Date Created	
    Case Number (Regarding) (Case)	
    Direction	
    Owner

Sheet 3, Email View:
    From (Object) (Email)	
    Current Sender (Object) (Email)	
    Case Number (Object) (Email)	
    Email Message Status (Object) (Email)	
    Entered Queue	
    Regarding (Object) (Email)	
    Case Owner User (Object) (Email)

Sheet 4, Phone Call View:
    Subject	
    Regarding	
    Case Number (Regarding) (Case)	
    Activity Type	
    Activity Status	
    Owner	
    Date Created	
    Primary Email (Owning User) (User)


First step is to compare all the case numbers from the channel sheets and compare to the PA Cases sheet case numbers mark those matched from sms emails phone calls

The matched cases will be the total case numbers for each channel. if a case is not found in sms or emails or phone call sheets and final action is from the reached metrics mark as an expected call channel

Then According to Final Action column in PA Cases sheet we will determine the outcome of each reach attempt (sms - email - phone call)

Final action options are:
    Fixed
    Refused Callback
    Issue Not Fixed
    Not yet Tested
    Escalation
    Sent SMS
    Sent Email
    Left VM
    Reviewed
    Bank/Sutherland
    Not Reached
    DND

For each attemp channel i want to calculate the outcome of each outcome. 

another metrics is reached / not reached
Reached is when the case is final action marked [Fixed, Issue Not Fixed, Not Yet Tested, Escalation,DND]
Not Reached is when the case is final action marked [Sent SMS, Sent Email, Left VM, Reviewed, Bank/Sutherland, Not Reached]

The output file should contain the following:
    Total Cases Sheet with coloumns:
    Case Number
    Work Order Type
    Incomming Channel
    Completion Date
    Final Action
    Matching Channel (sms - email - confirmd call - expected call)
    Serial Number

    Metrics
    Here i want an overview with tables and charts of all and everything that might be required
    include a table and chart for:
    each channel final action 
    each channel reach rate
    add any expected to be required metrics

If time frame is chosen (start date and end date) then the tool should only consider cases that are within that time frame. using the following
Column in PA Cases sheet:
    Completion Date
Column in SMS View:
    Date Created
Column in Email View:
    Entered Queue
Column in Phone Call View:
    Date Created


Metrics Update

When adding metrics 
Monthly breakdown is missing from the output might be broken in the code. Make sure the add the monthly breakdown as requested and referenced in the attached picture (percentage calculated is the number over the GT (Grand total))
I want several breakdowns 

Breakdown 1: Total Numbers
Month    | SMS                | Emails                 | Calls (expected + confirmed)  | Grand Total 
Month 1 | No. of matching SMS | No. of matching emails | No. of total calls            | Grand Total of cases on Month
Month 2 | No. of matching SMS | No. of matching emails | No. of total calls            | Grand Total of cases on Month
..
..
GT      | GT of SMS           | GT of Emails           | GT of Calls                   | Grand Total of months

Breakdown 2: Reached vs Not Reached
Month    | SMS reached | SMS not reached || Emails reached | Emails not reached || Calls (expected + confirmed) reached | calls not reached || Grand Total 
Month 1 | No. of matching SMS reached | SMS not reached || No. of matching emails reached | emails not reached  || No. of total calls reached | not reached  || Grand Total of cases on Month
Month 2 | No. of matching SMS reached | SMS not reached || No. of matching emails reached | emails not reached || No. of total calls reached | not reached || Grand Total of cases on Month
..
..
GT      | GT of SMS           | GT of Emails           | GT of Calls                   | Grand Total of months

Breakdown 3: Each Channel reach rate
Month    | SMS reached        | Emails  reached        | Calls (expected + confirmed) reached | Grand Total 
Month 1  | No. of matching SMS| No. of matching emails | No. of total calls                   | Grand Total of reached cases on Month
Month 2 | No. of matching SMS | No. of matching emails | No. of total calls                   | Grand Total of reached cases on Month
..
..
GT      | GT of SMS           | GT of Emails           | GT of Calls                   | Grand Total of months

Breakdown 4: Work Order Type reach channels
The same table for each Work Order Type (Onsite - Depot - CRU)
Month   | SMS reached        | Emails  reached        | Calls (expected + confirmed) reached | Grand Total 
Month 1 | No. of matching SMS| No. of matching emails | No. of total calls                   | Grand Total of reached cases on Month
Month 2 | No. of matching SMS| No. of matching emails| No. of total calls                    | Grand Total of reached cases on Month
..
..
GT      | GT of SMS           | GT of Emails           | GT of Calls                   | Grand Total of months