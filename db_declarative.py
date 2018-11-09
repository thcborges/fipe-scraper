import datetime
from time import sleep

from sqlalchemy import Column, ForeignKey, Integer, String, Date, SMALLINT, Float
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

UNVISITED = 1
VISITED = 2
VISITING = 3

ENGINE = 'postgres+psycopg2://user:password@localhost:5432/fipe'


class Referencia(Base):
    __tablename__ = 'referencia'
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(15))
    period = Column(Date, nullable=False)
    status = Column(SMALLINT, default=1)

    def __str__(self):
        return 'Referencia: (id: {}, period: {}, status: {})'.format(self.id, self.status, self.status)

    def __repr__(self):
        return 'Referencia: (id: {}, period: {}, status: {})'.format(self.id, self.period, self.status)


class Marca(Base):
    __tablename__ = 'marca'
    id = Column(Integer, primary_key=True, autoincrement=True)
    marca_name = Column(String(45), nullable=False, unique=True)
    status = Column(SMALLINT, default=1)

    def __str__(self):
        return 'Marca: (id: {}, name: {}, status: {})'.format(
            self.id, self.marca_name, self.status
        )

    def __repr__(self):
        return 'Marca: (id: {}, name: {}, status: {})'.format(
            self.id, self.marca_name, self.status
        )


class MarcaReferencia(Base):
    __tablename__ = 'marca_referencia'
    id = Column(Integer, primary_key=True, autoincrement=True)
    reference_id = Column(Integer, ForeignKey('referencia.id'))
    marca_id = Column(Integer, ForeignKey('marca.id'))

    def __str__(self):
        return 'MarcaReferencia: (reference_id: {}, marca_id:{})'.format(
            self.reference_id, self.marca_id
        )

    def __repr__(self):
        return 'MarcaReferencia: (reference_id: {}, marca_id:{})'.format(
            self.reference_id, self.marca_id
        )


class Modelo(Base):
    __tablename__ = 'modelo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    modelo_name = Column(String(45), nullable=False)
    fipe_code = Column(String(10))
    status = Column(SMALLINT, default=1)
    marca_id = Column(Integer, ForeignKey('marca.id'))

    def __str__(self):
        return 'Modelo: (id: {}, name: {}, codigo_fipe: {}, status: {}, marca_id: {})'.format(
            self.id, self.modelo_name, self.fipe_code, self.status, self.marca_id
        )

    def __repr__(self):
        return 'Modelo: (id: {}, name: {}, codigo_fipe: {}, status: {}, marca_id: {})'.format(
            self.id, self.modelo_name, self.fipe_code, self.status, self.marca_id
        )


class AnoModelo(Base):
    __tablename__ = 'ano_modelo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ano_modelo = Column(String(20))
    year = Column(Date)
    modelo = Column(String(45), nullable=False)
    status = Column(Integer, default=1)
    modelo_id = Column(Integer, ForeignKey('modelo.id'))

    def __str__(self):
        return 'AnoModelo: (id: {}, ano_modelo: {}, modelo_id: {}, status: {})'.format(
            self.id, self.modelo, self.modelo_id, self.status
        )

    def __repr__(self):
        return 'AnoModelo: (id: {}, ano_modelo: {}, modelo_id: {}, status: {})'.format(
            self.id, self.modelo, self.modelo_id, self.status
        )


class Price(Base):
    __tablename__ = 'price'
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_ano_modelo = Column(Integer, ForeignKey('ano_modelo.id'))
    id_referencia = Column(Integer, ForeignKey('referencia.id'))
    value = Column(Float)


class Database:
    engine = create_engine(ENGINE)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    def close(self):
        self.session.close()
        del self

    def save_database(self, data):
        try:
            self.session.add(data)
            self.session.commit()
        except Exception as error:
            print(error)
            pause()
            self.save_database(data)

    def save_reference(self, reference_list):
        if self.has_unvisited_reference() or self.reference_count() == 0:
            for period in reference_list:
                aux = period.split('/')
                months_list = {'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
                               'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}
                month = months_list[aux[0]]
                year = int(aux[1])
                date = datetime.date(year, month, 1)
                if self.has_not_reference(date):
                    reference = Referencia(period=date, text=period)
                    self.save_database(reference)

    def reference_count(self) -> int:
        query = self.session.query(Referencia).count()
        return query

    def has_not_reference(self, period) -> bool:
        query = self.session.query(Referencia).filter(Referencia.period == period).count()
        if query == 0:
            return True
        return False

    def has_unvisited_reference(self) -> bool:
        query = self.session.query(Referencia).filter(Referencia.status == UNVISITED).count()
        if query > 0:
            return True
        return False

    def get_unvisted_reference(self) -> Referencia:
        query = self.session.query(Referencia).filter(Referencia.status == UNVISITED).first()
        return query

    def has_marca_unvisited(self) -> bool:
        query = self.session.query(Marca).filter(Marca.status == UNVISITED).count()
        if query > 0:
            return True
        return False

    def has_marca(self, name) -> bool:
        query = self.session.query(Marca).filter(Marca.marca_name == name).count()
        if query > 0:
            return True
        return False

    def set_unvisited_marca(self, name: str):
        marca = self.session.query(Marca).filter(Marca.marca_name == name).one()
        marca.status = UNVISITED
        self.save_database(marca)

    def get_marca_id(self, name: str) -> int:
        query = self.session.query(Marca).filter(Marca.marca_name == name).one()
        return query.id

    def save_marcas(self, marca_list: list, reference_id: int):
        for marca in marca_list:
            if self.has_marca(marca):
                self.set_unvisited_marca(marca)
                marca_id = self.get_marca_id(marca)
            else:
                new_marca = Marca(marca_name=marca)
                self.save_database(new_marca)
                marca_id = new_marca.id
            reference_marca = MarcaReferencia(reference_id=reference_id, marca_id=marca_id)
            self.save_database(reference_marca)

    def get_unvisted_marca(self, ref_id: int) -> Marca:
        query = self.session.query(Marca).join(MarcaReferencia, Marca.id == MarcaReferencia.marca_id). \
            filter(Marca.status == UNVISITED, MarcaReferencia.reference_id == ref_id).order_by(Marca.id).first()
        return query

    def save_modelos(self, modelo_list: list, marca_id: int):
        for modelo in modelo_list:
            if self.has_modelo(modelo):
                self.set_unvisted_modelo(modelo)
            else:
                new_modelo = Modelo(modelo_name=modelo, marca_id=marca_id)
                self.save_database(new_modelo)

    def has_modelo(self, name: str) -> bool:
        query = self.session.query(Modelo).filter(Modelo.modelo_name == name).count()
        if query > 0:
            return True
        return False

    def set_unvisted_modelo(self, name: str):
        modelo = self.session.query(Modelo).filter(Modelo.modelo_name == name).one()
        modelo.status = UNVISITED
        self.save_database(modelo)

    def has_unvisited_modelo(self) -> bool:
        query = self.session.query(Modelo).filter(Modelo.status == UNVISITED).count()
        if query > 0:
            return True
        return False

    def get_unvisited_modelo(self, marca_id: int) -> Modelo:
        query = self.session.query(Modelo).filter(Modelo.status == UNVISITED, Modelo.marca_id == marca_id).order_by(
            Modelo.modelo_name).first()
        return query

    def has_unvisited_ano(self) -> bool:
        query = self.session.query(AnoModelo).filter(AnoModelo.status == UNVISITED).count()
        if query > 0:
            return True
        return False

    def save_anos(self, ano_list: list, modelo_id: int, period: datetime.date):
        for ano_modelo in ano_list:
            aux = ano_modelo.split(' ')
            try:
                ano = datetime.date(int(aux[0]), 1, 1)
            except ValueError:
                ano = period
            modelo = aux[1]
            new_ano = AnoModelo(ano_modelo=ano_modelo, year=ano, modelo=modelo, modelo_id=modelo_id)
            self.save_database(new_ano)

    def get_unvisited_ano(self, modelo_id: int) -> AnoModelo:
        query = self.session.query(AnoModelo) \
            .filter(AnoModelo.status == UNVISITED, AnoModelo.modelo_id == modelo_id).first()
        return query

    def set_modelo_visited(self, modelo_id: int):
        modelo = self.session.query(Modelo).filter(Modelo.id == modelo_id).one()
        modelo.status = VISITED
        self.save_database(modelo)

    def set_ano_visited(self, ano_id: int):
        ano = self.session.query(AnoModelo).filter(AnoModelo.id == ano_id).one()
        ano.status = VISITED
        self.save_database(ano)

    def set_marca_visited(self, marca_id: int):
        marca = self.session.query(Marca).filter(Marca.id == marca_id).one()
        marca.status = VISITED
        self.save_database(marca)

    def set_reference_visited(self, reference_id: int):
        ref = self.session.query(Referencia).filter(Referencia.id == reference_id).one()
        ref.status = VISITED
        self.save_database(ref)

    def delete_ano(self, ano_id: int):
        ano_modelo = self.session.query(AnoModelo).filter(AnoModelo.id == ano_id).first()
        print(ano_modelo, 'deleted')
        self.session.delete(ano_modelo)
        self.session.commit()


def pause():
    sleep(1)


if __name__ == '__main__':
    engine = create_engine(ENGINE)
    Base.metadata.create_all(engine)
