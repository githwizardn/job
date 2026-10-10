# JobRadar

ვაკანსიების აგრეგატორი საქართველოდან — აგროვებს ვაკანსიებს ქართული და გლობალური წყაროებიდან, ფილტრავს გეოგრაფიულად.

## ფუნქციები

- jobspy (LinkedIn/Indeed/Glassdoor/Google), jobs.ge, hr.ge + doctor.ge, jobs.ss.ge, Remotive
- გეო-ფილტრი — მხოლოდ ვაკანსიები, სადაც საქართველოდან მუშაობა შესაძლებელია
- Cross-site დედუპლიკაცია
- CSV ექსპორტი

## დაყენება

```bash
git clone https://github.com/gitwizardn/job.git
cd job
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
streamlit run app.py