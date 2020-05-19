# ChillBackend

* the backend for the HO_CHILL_TRIP project  
* 
________________________________________________________________________________________________________________
># Rundown  

1. to get all of the attraction and store it to the list  
2. to get all of the plan and create the Plan.Plan class  
3. classify the plan, like the below:  
    1. the plan need to gen and no must-go place  
    2. the plan need to gen and exist must-go list  
    3. the plan need to re-gen  
4. gen the route but it all depends, like the below:
    1. to handle case 3.1:
        1. find how many travel day of the plan
        2. gen the route depend on the day is first day or not (for different initial).
        3. recommend attraction by rating and distance
        4. if the time after 1830, the the generator will be ended and go back hotel
    2. to handle case 3.2:
        1. find how many travel day of the plan
        2. gen the route depend on the day is first day or not (for different initial).
        3. recommend attraction by rating and distance
        4. if there are no attraction in must-go list, then use the case 4.1 to handle rest
        5. if the time after 1830, the the generator will be ended and go back hotel
    3. to handle case 3.3:
        1. store all the attraction first
        2. find how many travel day of the plan
        3. gen the route depend on the day is first day or not (for different initial).
        4. recommend attraction by rating and distance
        5. if the recommended attraction is exist in the original attraction list, find the other attraction.  
        6. if the time after 1830, the the generator will be ended and go back hotel

`synchronize with the database every 5 sec`
________________________________________________________________________________________________________________
>## TODO / BUGS  
### IMPORTANT  
- [ ] 1. don't insert hotel with placeOrder: 1  
- [ ] 2. fix place duplicate (remember set bigger radius)  
- [ ] 3. generate plan (not 乜都冇plan)  
- [ ] 4. add driving route  
  
### LESS IMPORTANT  
- [ ] 5. use auto increment in attraction table  
- [ ] 6. other冇咁重要嘅 backend  
________________________________________________________________________________________________________________
