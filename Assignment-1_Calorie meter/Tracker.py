################   "Priya", 29/10/25 , "calorie tracker" #################
print("_____________________@@@@@WELCOME TO TEST YOUR CALORIE INTAKE@@@@@@@_______")
print()
Lm=[]
Lc=[]
while True:
    meal_nm=input("Enter your preferred meal:")
    Lm.append(meal_nm)
    calo_am=float(input("Enter the calorie amount the meal contains:"))
    Lc.append(calo_am)
    ch=input("Do you want to enter more data(y/n)?")
    if ch=='n':
        break
total=sum(Lc)
print("Total calories consumed in a day:",total)
avg=total/len(Lc)
print("Average no of calories consumed in a day:",avg)
val=float(input("Enter your intake of calories in a day:"))
if val>avg:
    print("NOT GOOD,ALARMING!!!!!")
elif val==avg:
    print("NOT BAD!!!!")
else:
    print("NICE,IN CONTROL!!!!!!")

print("Meal list:",Lm)
print("Calorie list:",Lc)
print()
print("__________________Here's the tabular form of the data_______________")
data =[
    ("Meal List", "Calories"),  
    ("Breakfast",350 ),
    ("Lunch",600),
    ("Dinner",150),
]
format_string = "{:<10} {:>10}"
print(format_string.format(data[0][0],data[0][1]))

print("-"*20)
for row in data[1:]:
    print(format_string.format(row[0], row[1]))
print(f"Average {avg:.2f}")
    
print()
print("JOB DONE,SUCCESSFULLY")
    
    
    
