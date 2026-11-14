from app import create_app, db
from model import State, LGA

NIGERIA_LOCATIONS = {
    "Cross River": {
        "code": "CR",
        "lgas": ["Calabar Municipal", "Calabar South", "Akpabuyo", "Bakassi", "Biase", "Boki", "Etung", "Ikom", "Obanliku", "Obubra", "Obudu", "Odukpani", "Ogoja", "Yakuur", "Yala"]
    },
    "Lagos": {
        "code": "LA",
        "lgas": ["Agege", "Ajeromi-Ifelodun", "Alimosho", "Amuwo-Odofin", "Apapa", "Epe", "Eti-Osa", "Ibeju-Lekki", "Ifako-Ijaiye", "Ikeja", "Ikorodu", "Lagos Island", "Lagos Mainland", "Mushin", "Ojo", "Oshodi-Isolo", "Shomolu", "Surulere"]
    },
    "Federal Capital Territory": {
        "code": "FC",
        "lgas": ["Abaji", "Bwari", "Gwagwalada", "Kuje", "Kwali", "Municipal Area Council (AMAC)"]
    },
    "Rivers": {
        "code": "RV",
        "lgas": ["Port Harcourt", "Obio/Akpor", "Eleme", "Ikwerre", "Okrika", "Degema", "Bonny"]
    }
}

def seed_database():
    app = create_app()
    with app.app_context():
        print("Starting location seeding for Nigeria...")
        for state_name, data in NIGERIA_LOCATIONS.items():
            state = State.query.filter_by(name=state_name).first()
            if not state:
                state = State(name=state_name, code=data["code"])
                db.session.add(state)
                db.session.commit()
                print(f"Added State: {state_name}")
            for lga_name in data["lgas"]:
                existing_lga = LGA.query.filter_by(state_id=state.id, name=lga_name).first()
                if not existing_lga:
                    lga = LGA(state_id=state.id, name=lga_name)
                    db.session.add(lga)
            db.session.commit()
            print(f"Seeded LGAs for {state_name}")
        print("Location seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
