1. SmartWait for elements to be visible and clickable instead of explicit wait and automatic smart retry on each failed (after timeout) element click or not found
2. Dialogs
    Complexity for case reviewer and Company email template preview and percase feedback
    Dark Mode & Accessibilty
3. Documentation (inline comments around the code)
4. Code Duplication (base dialogs to be common and used for all dialogs in the tool and then updates applied to the body content)
5. Deployment Scripts to run on code and start building the .spec file of ART Q Master
6. Progress indicator during autosender process
    Including action buttons like
        Pause to pause the process on the current element / step 
        Resume atfer the pause
        Stop to stop the process/loop after the current case and end the process
        Abort to kill the process and end the application right on the click
        Central Logging for errors and success confirmation
7. Isolate Company Process (not autorun after autosender) 
    add a button with auto sender & Case reviewer in dispatcher menu
8. Better Cache resume confirmation dialogue 
    Counts in the progress indicator what is left or the rest of cases to work on not to count the total cases after resume
9. Previous Case Feature fix (currently not working) and improve navigation breadcrumb 
10. Disable Keyboard entries on dialog to avoid keyboard entries on sudden popups while working on another window
11. Company metadata (Name - Company Name - Email - State/provice - local time)
    Data can be found in the excel sheet being used 
    Local time for the state/provice will be gained by adding a table inside the code with the offset to the current time and UTC for each (hardcoded in the code .py)
    Table Below:
Region	| Offset	| NOW()-3:00
Alabama	5:00:00 AM	Offset - (NOW()- 3:00)
Alaska	4:00:00 AM	Offset - (NOW()- 3:00)
Arizona	8:00:00 AM	Offset - (NOW()- 3:00)
Arkansas	6:00:00 AM	Offset - (NOW()- 3:00)
California	5:00:00 AM	Offset - (NOW()- 3:00)
Colorado	7:00:00 AM	Offset - (NOW()- 3:00)
Connecticut	6:00:00 AM	Offset - (NOW()- 3:00)
Delaware	4:00:00 AM	Offset - (NOW()- 3:00)
Florida	4:00:00 AM	Offset - (NOW()- 3:00)
Georgia	4:00:00 AM	Offset - (NOW()- 3:00)
Hawaii	6:00:00 AM	Offset - (NOW()- 3:00)
Idaho	4:00:00 AM	Offset - (NOW()- 3:00)
Illinois	5:00:00 AM	Offset - (NOW()- 3:00)
Indiana	6:00:00 AM	Offset - (NOW()- 3:00)
Iowa	4:00:00 AM	Offset - (NOW()- 3:00)
Kansas	4:00:00 AM	Offset - (NOW()- 3:00)
Kentucky	5:00:00 AM	Offset - (NOW()- 3:00)
Louisiana	5:00:00 AM	Offset - (NOW()- 3:00)
Maine	5:00:00 AM	Offset - (NOW()- 3:00)
Maryland	5:00:00 AM	Offset - (NOW()- 3:00)
Massachusetts	6:00:00 AM	Offset - (NOW()- 3:00)
Michigan	4:00:00 AM	Offset - (NOW()- 3:00)
Minnesota	5:00:00 AM	Offset - (NOW()- 3:00)
Mississippi	6:00:00 AM	Offset - (NOW()- 3:00)
Missouri	4:00:00 AM	Offset - (NOW()- 3:00)
Montana	6:00:00 AM	Offset - (NOW()- 3:00)
Nebraska	4:00:00 AM	Offset - (NOW()- 3:00)
Nevada	5:00:00 AM	Offset - (NOW()- 3:00)
New Hampshire	5:00:00 AM	Offset - (NOW()- 3:00)
New Jersey	6:00:00 AM	Offset - (NOW()- 3:00)
New Mexico	4:00:00 AM	Offset - (NOW()- 3:00)
New York	4:00:00 AM	Offset - (NOW()- 3:00)
North Carolina	4:00:00 AM	Offset - (NOW()- 3:00)
North Dakota	5:00:00 AM	Offset - (NOW()- 3:00)
Ohio	5:00:00 AM	Offset - (NOW()- 3:00)
Oklahoma	6:00:00 AM	Offset - (NOW()- 3:00)
Oregon	4:00:00 AM	Offset - (NOW()- 3:00)
Pennsylvania	5:00:00 AM	Offset - (NOW()- 3:00)
Rhode Island	6:00:00 AM	Offset - (NOW()- 3:00)
South Carolina	4:00:00 AM	Offset - (NOW()- 3:00)
South Dakota	4:00:00 AM	Offset - (NOW()- 3:00)
Tennessee	4:00:00 AM	Offset - (NOW()- 3:00)
Texas	5:00:00 AM	Offset - (NOW()- 3:00)
Utah	6:00:00 AM	Offset - (NOW()- 3:00)
Vermont	4:00:00 AM	Offset - (NOW()- 3:00)
Virginia	4:00:00 AM	Offset - (NOW()- 3:00)
Washington	5:00:00 AM	Offset - (NOW()- 3:00)
West Virginia	6:00:00 AM	Offset - (NOW()- 3:00)
Wisconsin	4:00:00 AM	Offset - (NOW()- 3:00)
Wyoming	4:00:00 AM	Offset - (NOW()- 3:00)
Alberta	5:00:00 AM	Offset - (NOW()- 3:00)
British Columbia	6:00:00 AM	Offset - (NOW()- 3:00)
Manitoba	4:00:00 AM	Offset - (NOW()- 3:00)
New Brunswick	4:00:00 AM	Offset - (NOW()- 3:00)    

12. Show spinner while initializing
13. Ensure application closure after any crash (chrome closing - driver closure - whatever) to end the code and process 
    as sometimes when chrome is closed or crashed the driver stays working and dialogs (casereviewer or whatever is proceeding) and add a pop up that the Tool ended and give option to return to Main Menu (before dispatcher) or Gracefull quit
