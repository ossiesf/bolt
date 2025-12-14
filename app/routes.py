from app.database import SessionLocal, URLMapping

class Routes:

    def save(self, short_code: str, url: str):
        session = SessionLocal()
        try:
            url_mapping = URLMapping(short_code=short_code, original_url=url)
            session.add(url_mapping)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get(self, short_code: str):
        session = SessionLocal()
        try:
            mapping = session.query(URLMapping).filter(URLMapping.short_code == short_code).first()
            return mapping.original_url if mapping else None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete(self, short_code: str):
        session = SessionLocal()
        try:
            mapping = session.query(URLMapping).filter(URLMapping.short_code == short_code).first()
            if mapping:
                session.delete(mapping)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def exists(self, short_code: str):
        session = SessionLocal()
        try:
            mapping = session.query(URLMapping).filter(short_code == short_code).first()
            return mapping is not None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()