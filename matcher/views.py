from django.shortcuts import render
from .forms import UploadCSVForm
from django.shortcuts import redirect
import csv

def home(request):
    return render(request, 'matcher/home.html', {
        "studentFileName": request.session.get("studentFileName", ""),
        "employerFileName": request.session.get("employerFileName", "")
    })
    
def upload_student_csv(request):
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]

            if not file.name.endswith(".csv"):
                return render(request, 'matcher/home.html', {
                    "form": form,
                    "error": "The file must be a .csv file.",
                    "studentFileName": request.session.get("studentFileName", ""),
                    "employerFileName": request.session.get("employerFileName", "")
                })
            request.session["studentData"] = parse_csv_file(file)
            request.session["studentFileName"] = file.name
            return redirect("home")
    return redirect("home")
        
def upload_employer_csv(request):
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)

        if form.is_valid():
            file = request.FILES["file"]

            if not file.name.endswith(".csv"):
                return render(request, 'matcher/home.html', {
                    "form": form,
                    "error": "The files must be .csv files.",
                    "studentFileName": request.session.get("studentFileName", ""),
                    "employerFileName": request.session.get("employerFileName", "")
                })
            request.session["employerData"] = parse_csv_file(file)
            request.session["employerFileName"] = file.name
            return redirect("home")
    return redirect("home")


def make_matches(students, employers):
# def make_matches(studentCsvFile, employerCsvFile):
    # students = parse_csv_file(studentCsvFile)
    # employers = parse_csv_file(employerCsvFile)

    matches = {}

    unmatchedStudents = []
    tryAgainStudents = []

    # Make an initial placement for all students a single time.
    for student in students:
        for employer in students[student]:
            if employer not in matches:
                matches[employer] = []

            # See if the student is on the employer’s list.
            if student in employers[employer]:
                
            # Case where there is still room to add the student, regardless of ranking.
                if len(matches[employer]) < int(employers[employer][0]):
                    matches[employer].append(student)
                    break
                
                # Case where the company is already at max capacity
                else:
                    lowestStudent = 0
                    for matchedStudent in matches[employer]:
                        currStudent = employers[employer].index(matchedStudent)
    
                        if currStudent > lowestStudent:
                            lowestStudent = currStudent
                    
                    # Case where current student is preferred over another student.
                    if employers[employer].index(student) < lowestStudent:
                        tryAgainStudents.append(employers[employer][lowestStudent])
                        matches[employer].remove(employers[employer][lowestStudent])
                        matches[employer].append(student)
                        break
                
    # Try to place all displaced students, otherwise move them to the unmatched students list.
    while len(tryAgainStudents) > 0:
        currStudent = tryAgainStudents[0]
        for employer in students[currStudent]:

            # See if the student is on the employer’s list.
            if currStudent in employers[employer]:
                
                # Case where there is still room to add the student, regardless of ranking.
                if len(matches[employer]) < int(employers[employer][0]):
                    matches[employer].append(currStudent)
                    tryAgainStudents.pop(0)
                    break
                
                # Case where the company is already at max capacity
                else:
                    lowestStudent = 0
                    for matchedStudent in matches[employer]:
                        iCurrStudent = employers[employer].index(matchedStudent)
                        if iCurrStudent > lowestStudent:
                            lowestStudent = iCurrStudent

                    # Case where current student is preferred over another student.
                    if employers[employer].index(currStudent) < lowestStudent:
                        tryAgainStudents.append(employers[employer][lowestStudent])
                        tryAgainStudents.pop(0)
                        matches[employer].remove(employers[employer][lowestStudent])
                        matches[employer].append(currStudent)
                        break
        
        # If the try again student wasn't placed by this point, then there is no match for them.
        if currStudent in tryAgainStudents:
            unmatchedStudents.append(currStudent)
            tryAgainStudents.pop(tryAgainStudents.index(currStudent))
    
    return matches

def parse_csv_file(file):
    decoded = file.read().decode('utf-8').splitlines()
    reader = csv.reader(decoded)
    next(reader)

    parsedData = {}
    for row in reader:
        parsedData[row[1]] = row[2:]

    return parsedData

def generate_report(request):
    employer_file = request.session.get("employerData")
    student_file = request.session.get("studentData")

    if not employer_file or not student_file:
        return render(request, "matcher/home.html", {
            "error": "Please upload both files.",
            "studentFileName": request.session.get("studentFileName", ""),
            "employerFileName": request.session.get("employerFileName", "")
        })
    
    matches = make_matches(student_file, employer_file)

    return render(request, "matcher/report.html", {
        "matches": matches
    })

def clear_student_file(request):
    del request.session["studentFileName"]
    del request.session["studentData"]
    return redirect("home")

def clear_employer_file(request):
    del request.session["employerFileName"]
    del request.session["employerData"]
    return redirect("home")