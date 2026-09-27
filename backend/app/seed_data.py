from datetime import date, datetime
from app.database import SessionLocal
from app.models import Member, Vegetable, PlantingCalendar, Recipe


def seed_database():
    db = SessionLocal()

    try:
        if db.query(Member).count() == 0:
            members = [
                Member(
                    name="张农人",
                    email="farmer@csa.com",
                    phone="13800138001",
                    role="farmer",
                    is_active=True
                ),
                Member(
                    name="李消费者",
                    email="consumer1@csa.com",
                    phone="13800138002",
                    role="consumer",
                    is_active=True,
                    preferences={"taste": "清淡", "allergies": ["花生"]}
                ),
                Member(
                    name="王会员",
                    email="consumer2@csa.com",
                    phone="13800138003",
                    role="consumer",
                    is_active=True,
                    preferences={"taste": "香辣", "diet": "素食"}
                )
            ]
            db.add_all(members)
            db.commit()
            print("会员数据已初始化")

        if db.query(Vegetable).count() == 0:
            vegetables = [
                Vegetable(
                    name="番茄",
                    english_name="Tomato",
                    season="summer",
                    planting_start=date(2026, 3, 15),
                    planting_end=date(2026, 4, 30),
                    harvest_start=date(2026, 6, 1),
                    harvest_end=date(2026, 9, 30),
                    description="本地有机种植，酸甜多汁",
                    nutritional_value="富含维生素C和番茄红素",
                    storage_method="阴凉处保存，避免冷藏",
                    share_quota=100,
                    is_available=True
                ),
                Vegetable(
                    name="黄瓜",
                    english_name="Cucumber",
                    season="summer",
                    planting_start=date(2026, 4, 1),
                    planting_end=date(2026, 5, 15),
                    harvest_start=date(2026, 6, 15),
                    harvest_end=date(2026, 9, 15),
                    description="脆嫩爽口，带刺新鲜",
                    nutritional_value="低热量，富含水分和维生素K",
                    storage_method="冰箱冷藏可保存3-5天",
                    share_quota=80,
                    is_available=True
                ),
                Vegetable(
                    name="青菜",
                    english_name="Chinese Cabbage",
                    season="autumn",
                    planting_start=date(2026, 8, 15),
                    planting_end=date(2026, 9, 30),
                    harvest_start=date(2026, 10, 15),
                    harvest_end=date(2026, 12, 31),
                    description="叶嫩梗绿，清甜可口",
                    nutritional_value="富含维生素A、C和膳食纤维",
                    storage_method="冰箱冷藏可保存5-7天",
                    share_quota=120,
                    is_available=True
                ),
                Vegetable(
                    name="萝卜",
                    english_name="Radish",
                    season="winter",
                    planting_start=date(2026, 9, 1),
                    planting_end=date(2026, 10, 15),
                    harvest_start=date(2026, 12, 1),
                    harvest_end=date(2027, 2, 28),
                    description="脆甜多汁，肉质紧密",
                    nutritional_value="富含维生素C和消化酶",
                    storage_method="阴凉通风处可保存1-2个月",
                    share_quota=90,
                    is_available=True
                ),
                Vegetable(
                    name="菠菜",
                    english_name="Spinach",
                    season="spring",
                    planting_start=date(2026, 2, 20),
                    planting_end=date(2026, 3, 31),
                    harvest_start=date(2026, 4, 15),
                    harvest_end=date(2026, 6, 10),
                    description="叶片肥厚，鲜嫩翠绿",
                    nutritional_value="富含铁、叶酸和维生素K",
                    storage_method="冰箱冷藏可保存2-3天",
                    share_quota=70,
                    is_available=True
                ),
                Vegetable(
                    name="茄子",
                    english_name="Eggplant",
                    season="summer",
                    planting_start=date(2026, 3, 20),
                    planting_end=date(2026, 5, 10),
                    harvest_start=date(2026, 7, 1),
                    harvest_end=date(2026, 9, 20),
                    description="皮紫肉嫩，口感细腻",
                    nutritional_value="富含维生素P和花青素",
                    storage_method="阴凉处保存，不宜冷藏",
                    share_quota=85,
                    is_available=True
                )
            ]
            db.add_all(vegetables)
            db.commit()
            print("蔬菜数据已初始化")

            vegetables = db.query(Vegetable).all()
            calendar_entries = []
            for veg in vegetables:
                if veg.planting_start:
                    calendar_entries.append(PlantingCalendar(
                        vegetable_id=veg.id,
                        activity_type="planting",
                        activity_date=veg.planting_start,
                        description=f"播种{veg.name}",
                        completed=veg.planting_start < date.today()
                    ))
                if veg.harvest_start:
                    calendar_entries.append(PlantingCalendar(
                        vegetable_id=veg.id,
                        activity_type="harvesting",
                        activity_date=veg.harvest_start,
                        description=f"开始收获{veg.name}",
                        completed=veg.harvest_start < date.today()
                    ))

            db.add_all(calendar_entries)
            db.commit()
            print("种植日历数据已初始化")

        if db.query(Recipe).count() == 0:
            recipes = [
                Recipe(
                    title="番茄炒蛋",
                    vegetables_used=["番茄"],
                    ingredients=[
                        {"name": "番茄", "quantity": "2个"},
                        {"name": "鸡蛋", "quantity": "3个"},
                        {"name": "葱花", "quantity": "适量"},
                        {"name": "盐", "quantity": "适量"},
                        {"name": "糖", "quantity": "少许"}
                    ],
                    steps=[
                        "番茄切块，鸡蛋打散",
                        "热锅下油，炒散鸡蛋盛出",
                        "锅内加油，炒番茄至出汁",
                        "加入盐和糖调味",
                        "倒入炒好的鸡蛋，翻炒均匀",
                        "撒上葱花即可出锅"
                    ],
                    cooking_time=15,
                    difficulty="简单"
                ),
                Recipe(
                    title="凉拌黄瓜",
                    vegetables_used=["黄瓜"],
                    ingredients=[
                        {"name": "黄瓜", "quantity": "2根"},
                        {"name": "大蒜", "quantity": "3瓣"},
                        {"name": "生抽", "quantity": "2勺"},
                        {"name": "香醋", "quantity": "1勺"},
                        {"name": "香油", "quantity": "少许"},
                        {"name": "辣椒油", "quantity": "可选"}
                    ],
                    steps=[
                        "黄瓜洗净拍碎切段",
                        "大蒜切末",
                        "将黄瓜放入碗中，加入蒜末",
                        "加入生抽、香醋、香油",
                        "喜欢辣的可以加辣椒油",
                        "拌匀后静置10分钟入味即可"
                    ],
                    cooking_time=20,
                    difficulty="简单"
                ),
                Recipe(
                    title="蒜蓉炒青菜",
                    vegetables_used=["青菜"],
                    ingredients=[
                        {"name": "青菜", "quantity": "500g"},
                        {"name": "大蒜", "quantity": "5瓣"},
                        {"name": "盐", "quantity": "适量"},
                        {"name": "食用油", "quantity": "适量"}
                    ],
                    steps=[
                        "青菜洗净沥干水分",
                        "大蒜切末",
                        "热锅下油，爆香蒜末",
                        "加入青菜大火快炒",
                        "青菜变软后加盐调味",
                        "翻炒均匀即可出锅"
                    ],
                    cooking_time=10,
                    difficulty="简单"
                )
            ]
            db.add_all(recipes)
            db.commit()
            print("食谱数据已初始化")

        print("数据库初始化完成！")

    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
