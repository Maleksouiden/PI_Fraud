from app import db

# Table d'association pour les compétences
profile_skills = db.Table('profile_skills',
    db.Column('profile_id', db.Integer, db.ForeignKey('profile.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"Skill('{self.name}')"

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Informations personnelles
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

    # Informations professionnelles
    title = db.Column(db.String(100))  # Titre professionnel
    years_experience = db.Column(db.Integer, default=0)
    education_level = db.Column(db.String(50))  # Niveau d'études

    # Préférences d'emploi
    desired_salary = db.Column(db.Integer)
    desired_location = db.Column(db.String(100))
    work_type = db.Column(db.String(20))  # Présentiel, télétravail, mixte

    # CV et photo
    resume_path = db.Column(db.String(255))
    photo_path = db.Column(db.String(255))

    # Relations
    skills = db.relationship('Skill', secondary=profile_skills, lazy='subquery',
                            backref=db.backref('profiles', lazy=True))

    def __repr__(self):
        return f"Profile('{self.first_name} {self.last_name}')"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def match_score(self, job):
        """Calcule un score de correspondance entre le profil et une offre d'emploi"""
        score = 0

        # Correspondance des compétences (moins stricte)
        profile_skills = {skill.name.lower() for skill in self.skills}
        job_skills = {skill.name.lower() for skill in job.skills}

        # Donner un score de base même sans compétences correspondantes
        score += 5  # 5% de score de base pour toutes les offres

        if profile_skills and job_skills:
            matching_skills = profile_skills.intersection(job_skills)
            if len(job_skills) > 0:
                skill_score = (len(matching_skills) / len(job_skills)) * 35  # 35% du score
                score += skill_score

            # Bonus si au moins une compétence correspond
            if matching_skills:
                score += 5  # 5% de bonus pour au moins une compétence correspondante

        # Correspondance du lieu (moins stricte)
        if self.desired_location and job.location:
            # Correspondance exacte
            if self.desired_location.lower() == job.location.lower():
                score += 15  # 15% du score
            # Correspondance partielle
            elif self.desired_location.lower() in job.location.lower() or job.location.lower() in self.desired_location.lower():
                score += 10  # 10% du score
            # Donner un petit score même sans correspondance
            else:
                score += 2  # 2% du score
        else:
            # Si l'un des deux est vide, donner un petit score
            score += 2  # 2% du score

        # Correspondance du type de travail (moins stricte)
        if self.work_type and job.work_type:
            # Correspondance exacte
            if self.work_type.lower() == job.work_type.lower():
                score += 15  # 15% du score
            # Le mixte correspond partiellement au présentiel et au télétravail
            elif (self.work_type.lower() == 'mixte' or job.work_type.lower() == 'mixte'):
                score += 8  # 8% du score
            # Donner un petit score même sans correspondance
            else:
                score += 2  # 2% du score
        else:
            # Si l'un des deux est vide, donner un petit score
            score += 2  # 2% du score

        # Correspondance du salaire (moins stricte)
        if self.desired_salary and job.salary:
            # Le salaire est supérieur ou égal à celui souhaité
            if job.salary >= self.desired_salary:
                score += 10  # 10% du score
            # Le salaire est proche (au moins 80% du salaire souhaité)
            elif job.salary >= (self.desired_salary * 0.8):
                score += 5  # 5% du score
            # Donner un petit score même si le salaire est inférieur
            else:
                score += 2  # 2% du score
        else:
            # Si l'un des deux est vide, donner un petit score
            score += 2  # 2% du score

        # Correspondance du niveau d'études (moins stricte)
        if self.education_level and job.education_required:
            # Correspondance exacte
            if self.education_level.lower() == job.education_required.lower():
                score += 10  # 10% du score
            # Niveau d'études supérieur à celui requis
            elif self._compare_education_levels(self.education_level, job.education_required) >= 0:
                score += 8  # 8% du score
            # Donner un petit score même si le niveau est inférieur
            else:
                score += 2  # 2% du score
        else:
            # Si l'un des deux est vide, donner un petit score
            score += 2  # 2% du score

        return min(100, score)  # Limiter le score à 100

    def _compare_education_levels(self, level1, level2):
        """Compare deux niveaux d'études et retourne la différence"""
        education_ranks = {
            'bac': 1,
            'bac+2': 2,
            'bac+3': 3,
            'bac+5': 5,
            'bac+8': 8
        }

        # Extraire le niveau numérique
        level1_clean = level1.lower().replace(' ', '')
        level2_clean = level2.lower().replace(' ', '')

        rank1 = education_ranks.get(level1_clean, 0)
        rank2 = education_ranks.get(level2_clean, 0)

        return rank1 - rank2  # Positif si level1 > level2, négatif si level1 < level2
