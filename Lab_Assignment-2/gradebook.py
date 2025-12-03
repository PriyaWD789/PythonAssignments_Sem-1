########################## PRIYA , 28/11/25 , GRADEBOOK_ANALYZER #################################
###########################@@@@@@@@@@ WELCOME !!!!!!!!!!@@@@@@@@@@@@ ##############################

d = {}
while True:
    name = input("Enter student's name:")
    marks = int(input("Enter student's marks: "))
    d[name] = marks
    ch = input("Do you want to enter more data(y/n)??")
    if ch == 'n':
        break

print("The required dictionary:", d)

# Convert to list
d_marks = list(d.values())
print("Marks list:", d_marks)

#####  average of the student's marks #####
def Calculate_average(d_marks):
    print("The average of total marks is:", sum(d_marks) / len(d_marks))

Calculate_average(d_marks)

##### median of student's marks  (FIXED) #####
def Calculate_median(d_marks):
    sorted_marks = sorted(d_marks)
    n = len(sorted_marks)
    if n % 2 == 1:   # odd
        med = sorted_marks[n // 2]
    else:            # even
        med = (sorted_marks[n // 2 - 1] + sorted_marks[n // 2]) / 2
    print("The median of marks is:", med)

Calculate_median(d_marks)

#### find max score ######
def find_max_score(d_marks):
    print("Maximum marks:", max(d_marks))

find_max_score(d_marks)

##### find min score #######
def find_min_score(d_marks):
    print("Minimum marks:", min(d_marks))

find_min_score(d_marks)

######## Assigning grades ############

grade_count = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
new_d = {}

for name, mark in d.items():
    if mark >= 90:
        grade = "A"
    elif mark >= 80:
        grade = "B"
    elif mark >= 70:
        grade = "C"
    elif mark >= 60:
        grade = "D"
    else:
        grade = "F"

    grade_count[grade] += 1   # counting fixed
    new_d[name] = grade       # new dictionary fixed

print("\nGrade-wise student count:")
print("A grade:", grade_count["A"])
print("B grade:", grade_count["B"])
print("C grade:", grade_count["C"])
print("D grade:", grade_count["D"])
print("F grade:", grade_count["F"])

print("\nNew dictionary with grades:", new_d)

##### PASS / FAIL (list comprehension) #####
passed_students = [name for name, mark in d.items() if mark >= 40]
failed_students = [name for name, mark in d.items() if mark < 40]

print("\nPassed students:", passed_students)
print("Failed students:", failed_students)

##### PRINTING RESULTS TABLE #####
print("\nName\tMarks\tGrade")
print("--------------------------------------")
for name, mark in d.items():
    print(f"{name}\t{mark}\t{new_d[name]}")
