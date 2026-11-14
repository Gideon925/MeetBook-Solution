from app import create_app
from app.extensions import db
from app.models import CatalogueItem


app = create_app()


CATALOGUE = {
    "Food": {
        "Rice Dishes": [
            "Jollof Rice",
            "Fried Rice",
            "White Rice",
            "Coconut Rice",
            "Ofada Rice",
            "Rice and Beans",
        ],
        "Swallow and Soups": [
            "Egusi Soup",
            "Afang Soup",
            "Edikang Ikong",
            "Ogbono Soup",
            "Okra Soup",
            "Banga Soup",
            "Vegetable Soup",
            "Oha Soup",
            "Efo Riro",
            "Fufu",
            "Pounded Yam",
            "Eba",
            "Semo",
            "Amala",
        ],
        "Proteins": [
            "Grilled Chicken",
            "Fried Chicken",
            "Turkey",
            "Beef",
            "Goat Meat",
            "Grilled Fish",
            "Fried Fish",
            "Peppered Snail",
            "Assorted Meat",
        ],
        "Fast Food": [
            "Shawarma",
            "Pizza",
            "Burger",
            "Sandwich",
            "Hot Dog",
            "French Fries",
            "Chicken and Chips",
        ],
        "Snacks and Small Chops": [
            "Meat Pie",
            "Sausage Roll",
            "Puff Puff",
            "Chin Chin",
            "Doughnut",
            "Spring Rolls",
            "Samosa",
            "Pepper Gizzard",
        ],
        "Drinks": [
            "Bottled Water",
            "Soft Drinks",
            "Fresh Juice",
            "Zobo",
            "Chapman",
            "Smoothie",
            "Milkshake",
        ],
        "Breakfast": [
            "Akara and Pap",
            "Moi Moi",
            "Bread and Egg",
            "Yam and Egg",
            "Pancakes",
            "Oatmeal",
        ],
    },

    "Home": {
        "Cleaning Services": [
            "House Cleaning",
            "Deep Cleaning",
            "Office Cleaning",
            "Post-Construction Cleaning",
        ],
        "Repairs and Maintenance": [
            "Plumbing",
            "Electrical Repairs",
            "Generator Repairs",
            "Air Conditioner Repairs",
            "Refrigerator Repairs",
            "Washing Machine Repairs",
            "Carpentry",
            "Furniture Repairs",
        ],
        "Home Assistance": [
            "Cooking at Home",
            "Laundry",
            "Ironing",
            "Painting",
            "Furniture Assembly",
            "Pest Control",
        ],
    },

    "Business": {
        "Hair and Beauty": [
            "Haircut",
            "Hair Styling",
            "Hair Braiding",
            "Makeup",
            "Manicure",
            "Pedicure",
        ],
        "Photography and Events": [
            "Photography",
            "Videography",
            "Event Planning",
            "Event Decoration",
        ],
        "Professional Services": [
            "Graphic Design",
            "Web Development",
            "Business Consultation",
            "Computer Repairs",
            "Printing Services",
        ],
    },

    "Connect": {
        "Social Connection": [
            "Social Conversation",
            "Online Companionship",
            "Voice Call Session",
            "Video Call Session",
            "In-Person Social Session",
        ],
    },

    "Moving": {
        "Moving Services": [
            "House Moving",
            "Office Moving",
            "Furniture Transportation",
            "Loading and Unloading",
            "Packing Services",
            "Unpacking Services",
        ],
    },

    "Pet Care": {
        "Pet Services": [
            "Pet Grooming",
            "Veterinary Visit",
            "Pet Sitting",
            "Pet Walking",
            "Pet Boarding",
            "Pet Feeding",
        ],
    },

    "Mobility": {
        "Transport Services": [
            "Personal Driver",
            "Car Hire",
            "Airport Pickup",
            "Airport Drop-off",
            "Scheduled Transport",
            "Point-to-Point Transport",
        ],
        "Roadside Assistance": [
            "Vehicle Towing",
            "Battery Jump Start",
            "Tyre Change",
            "Fuel Delivery",
            "Vehicle Recovery",
            "Car Breakdown Assistance",
        ],
    },

    "Health": {
        "Healthcare Services": [
            "Doctor Consultation",
            "Nursing Care",
            "Home Nursing Visit",
            "Clinic Appointment",
            "Physiotherapy",
            "Medical Laboratory Services",
        ],
    },
}


def seed_catalogue():
    added = 0

    with app.app_context():
        try:
            for division, categories in CATALOGUE.items():
                for category, names in categories.items():
                    for name in names:

                        existing = CatalogueItem.query.filter_by(
                            division=division,
                            category=category,
                            name=name,
                        ).first()

                        if existing:
                            continue

                        item = CatalogueItem(
                            division=division,
                            category=category,
                            name=name,
                            listing_type=(
                                "product"
                                if division == "Food"
                                else "service"
                            ),
                            is_active=True,
                        )

                        db.session.add(item)
                        added += 1

            db.session.commit()

            print("MeetBook catalogue setup completed.")
            print(f"New catalogue items added: {added}")
            print(f"Main divisions configured: {len(CATALOGUE)}")

        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    seed_catalogue()
