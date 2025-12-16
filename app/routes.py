from app.database import SessionLocal, Session, URLMapping

# Defining this outside the class so it can be imported via app.routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Routes:

    def save(self, short_code: str, url: str, db: Session):
        try:
            url_mapping = URLMapping(short_code=short_code, original_url=url)
            db.add(url_mapping)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    def get(self, short_code: str, db: Session):
        try:
            mapping = db.query(URLMapping).filter(URLMapping.short_code == short_code).first()
            return mapping.original_url if mapping else None
        except Exception as e:
            db.rollback()
            raise e

    def delete(self, short_code: str, db: Session):
        try:
            mapping = db.query(URLMapping).filter(URLMapping.short_code == short_code).first()
            if mapping:
                db.delete(mapping)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            raise e

    def exists(self, short_code: str, db: Session):
        try:
            mapping = db.query(URLMapping).filter(URLMapping.short_code == short_code).first()
            return mapping is not None
        except Exception as e:
            db.rollback()
            raise e