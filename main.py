from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from pydantic import BaseModel

Base = declarative_base()

class ElfCreate(BaseModel):
    name: str

class ItemCreate(BaseModel):
    name: str

class ItemAssignment(BaseModel):
    item_id: int
    elf_id: int

class ElfUpdate(BaseModel):
    is_on_leave: bool

class ItemAssignment(BaseModel):
    item_id: int
    elf_id: int

class Elf(Base):
    __tablename__ = "elves"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_available = Column(Boolean, default=True)
    is_on_leave = Column(Boolean, default=False)

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    elf_id = Column(Integer, ForeignKey("elves.id"))
    elf = relationship("Elf", back_populates="items")

Elf.items = relationship("Item", back_populates="elf")

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

@app.post("/elves/")
def create_elf(elf: ElfCreate):
    db = SessionLocal()
    elf_db = Elf(name=elf.name)
    db.add(elf_db)
    db.commit()
    db.refresh(elf_db)
    db.close()
    return elf_db

@app.get("/elves/")
def get_elves():
    db = SessionLocal()
    elves = db.query(Elf).all()
    db.close()
    return elves

@app.get("/elves/{elf_id}")
def read_elf(elf_id: int):
    db = SessionLocal()
    elf = db.query(Elf).filter(Elf.id == elf_id).first()
    db.close()
    if elf is None:
        raise HTTPException(status_code=404, detail="Elf not found")
    return elf

@app.post("/items/")
def create_item(item: ItemCreate):
    db = SessionLocal()
    item_db = Item(name=item.name)
    db.add(item_db)
    db.commit()
    db.refresh(item_db)
    db.close()
    return item_db

@app.get("/items/{item_id}")
def read_item(item_id: int):
    db = SessionLocal()
    item = db.query(Item).filter(Item.id == item_id).first()
    db.close()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/assign_item/")
def assign_item(assignment: ItemAssignment):
    db = SessionLocal()
    item = db.query(Item).filter(Item.id == assignment.item_id).first()
    elf = db.query(Elf).filter(Elf.id == assignment.elf_id).first()

    if item is None or elf is None:
        raise HTTPException(status_code=404, detail="Item or Elf not found")

    item.elf_id = elf.id
    elf.is_available = False  # Ustawienie elfa jako niedostępnego
    db.commit()
    db.close()
    return {"message": "Item assigned successfully"}

@app.put("/assign_leave/{elf_id}")
def assign_leave(elf_id: int, update_data: ElfUpdate):
    db = SessionLocal()
    elf = db.query(Elf).filter(Elf.id == elf_id).first()

    if elf is None:
        raise HTTPException(status_code=404, detail="Elf not found")

    elf.is_on_leave = update_data.is_on_leave

    # Zmiana wartości is_available na odwrotną
    elf.is_available = not update_data.is_on_leave

    db.commit()
    db.close()
    return {"message": f"Leave assigned for Elf {elf_id}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
