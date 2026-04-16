from django.shortcuts import render
from .forms import UploadCSVForm
from django.shortcuts import redirect
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from django.utils import timezone
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

    matches = {}

    matchedStudents = []
    unmatchedStudents = []
    tryAgainStudents = []

    # Make an initial placement for all students a single time.
    for student in students:
        matchedStudents.append(student)
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
            matchedStudents.remove(currStudent)
            tryAgainStudents.pop(tryAgainStudents.index(currStudent))

    all_students = set(students.keys())
    matched_students = set()

    for employer in matches:
        for student in matches[employer]:
            matched_students.add(student)

    unmatchedStudents = list(all_students - matched_students)

    matches = {
    employer: students
    for employer, students in matches.items()
    if students
}

    return matches, unmatchedStudents

def make_potential_matches(matches, employer_dict, unmatched_students):
    potential_matches = {}
    unmatched_set = set(unmatched_students)
    unmatched_companies = []

    for employer in employer_dict:
        capacity = int(employer_dict[employer][0])
        current_matches = matches.get(employer, [])

        if capacity > len(current_matches):
            valid_students = [
                student for student in employer_dict[employer][1:]
                if student in unmatched_set
            ]

            if valid_students:
                potential_matches[employer] = valid_students
        if not matches.get(employer):
            unmatched_companies.append(employer)

    for company in potential_matches:
        capacity = int(employer_dict[company][0])
        current = len(matches.get(company, []))
        potential_matches[company] = {
            "students": potential_matches[company],
            "open_spots": capacity - current
        }
    

    return potential_matches, unmatched_set, unmatched_companies

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
    
    matches, unmatched_students = make_matches(student_file, employer_file)

    potential_matches, unmatched_students_potential, unmatched_companies = make_potential_matches(matches, employer_file, unmatched_students)

    matches_data = {}
    for company in matches:
        capacity = int(employer_file[company][0])
        matches_data[company] = {
            "students": matches[company],
            "capacity": capacity
        }

    return render(request, "matcher/report.html", {
        "matches": matches_data,
        "potential_matches": potential_matches,
        "unmatched_students": unmatched_students_potential,
        "unmatched_companies": unmatched_companies,
        "employers": employer_file
    })

def clear_student_file(request):
    del request.session["studentFileName"]
    del request.session["studentData"]
    return redirect("home")

def clear_employer_file(request):
    del request.session["employerFileName"]
    del request.session["employerData"]
    return redirect("home")

from django.http import HttpResponse
from django.utils import timezone
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter


def download_report(request):
    employer_file = request.session.get("employerData")
    student_file = request.session.get("studentData")

    if not employer_file or not student_file:
        return HttpResponse("Missing data", status=400)

    matches, unmatched_students = make_matches(student_file, employer_file)

    potential_matches, unmatched_students, unmatched_companies = make_potential_matches(
        matches, employer_file, unmatched_students
    )

    # ✅ Build matches in same structure as template
    structured_matches = {}
    for company, students in matches.items():
        capacity = int(employer_file[company][0])
        structured_matches[company] = {
            "students": students,
            "capacity": capacity
        }

    # ✅ Filename with date
    today = timezone.now().strftime("%m.%d.%y")
    filename = f"report_{today}.pdf"

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(
    response,
    pagesize=letter,
    title="Downloaded Report"
)
    styles = getSampleStyleSheet()

    elements = []

    # Title
    elements.append(Paragraph("The Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    # Matches
    elements.append(Paragraph("Matches", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    for company, data in structured_matches.items():
        line = f"{company} → {', '.join(data['students'])}"
        elements.append(Paragraph(line, styles["Normal"]))
        elements.append(Spacer(1, 8))

    # Potential Matches
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Potential Matches", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "This is a list of possible matches where the employer had open spot(s) "
        "that were not initially filled and they listed a student in their rankings "
        "that did not get matched with a company. This ignores the student's top ten "
        "list since it did not get them a match, and gives them an opportunity to go "
        "with a company that wants them.",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 10))

    for company, data in potential_matches.items():
        elements.append(Paragraph(
            f"{company} has {data['open_spots']} open spot(s)",
            styles["Normal"]
        ))
        elements.append(Paragraph(
            f"Possible Students: {', '.join(data['students'])}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 12))

    # Unmatched Students
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Unmatched Students", styles["Heading3"]))
    elements.append(Spacer(1, 10))

    for student in unmatched_students:
        elements.append(Paragraph(student, styles["Normal"]))

    # Unmatched Companies
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Unmatched Companies", styles["Heading3"]))
    elements.append(Spacer(1, 10))

    for company in unmatched_companies:
        elements.append(Paragraph(company, styles["Normal"]))

    doc.build(elements)

    return response