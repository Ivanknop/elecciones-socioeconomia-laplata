"""Objetos de dominio para resultados electorales.

Se parsean a partir del JSON crudo devuelto por `electoral.client.ResultadosClient`.
Cada nivel guarda en `extra` los campos del JSON que no están modelados
explícitamente, para poder detectar campos nuevos o no documentados sin que
el parseo falle.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def _extra(raw: dict, conocidos: set[str]) -> dict:
    return {k: v for k, v in raw.items() if k not in conocidos}


@dataclass
class Lista:
    """Desglose por lista interna dentro de una agrupación.
    """

    nombre: str
    votos: int
    numero: str | None = None

    @classmethod
    def from_json(cls, raw: dict) -> "Lista":
        return cls(nombre=raw["nombre"], votos=raw["votos"], numero=raw.get("numero"))


@dataclass
class ValorAgrupacion:
    id_agrupacion: str
    nombre_agrupacion: str
    votos: int
    votos_porcentaje: float
    listas: list[Lista] = field(default_factory=list)
    extra: dict = field(default_factory=dict, repr=False)

    _CAMPOS_CONOCIDOS = {
        "idAgrupacion",
        "nombreAgrupacion",
        "votos",
        "votosPorcentaje",
        "listas",
    }

    @classmethod
    def from_json(cls, raw: dict) -> "ValorAgrupacion":
        return cls(
            id_agrupacion=str(raw["idAgrupacion"]),
            nombre_agrupacion=raw["nombreAgrupacion"].strip(),
            votos=raw["votos"],
            votos_porcentaje=raw["votosPorcentaje"],
            listas=[Lista.from_json(l) for l in raw.get("listas", [])],
            extra=_extra(raw, cls._CAMPOS_CONOCIDOS),
        )


@dataclass
class EstadoRecuento:
    mesas_esperadas: int
    mesas_totalizadas: int
    mesas_totalizadas_porcentaje: float
    cantidad_electores: int
    cantidad_votantes: int
    participacion_porcentaje: float
    extra: dict = field(default_factory=dict, repr=False)

    _CAMPOS_CONOCIDOS = {
        "mesasEsperadas",
        "mesasTotalizadas",
        "mesasTotalizadasPorcentaje",
        "cantidadElectores",
        "cantidadVotantes",
        "participacionPorcentaje",
    }

    @classmethod
    def from_json(cls, raw: dict) -> "EstadoRecuento":
        return cls(
            mesas_esperadas=raw["mesasEsperadas"],
            mesas_totalizadas=raw["mesasTotalizadas"],
            mesas_totalizadas_porcentaje=raw["mesasTotalizadasPorcentaje"],
            cantidad_electores=raw["cantidadElectores"],
            cantidad_votantes=raw["cantidadVotantes"],
            participacion_porcentaje=raw["participacionPorcentaje"],
            extra=_extra(raw, cls._CAMPOS_CONOCIDOS),
        )


@dataclass
class ValoresOtros:
    votos_nulos: int
    votos_nulos_porcentaje: float
    votos_en_blanco: int
    votos_en_blanco_porcentaje: float
    votos_recurridos_comando_impugnados: int
    votos_recurridos_comando_impugnados_porcentaje: float
    extra: dict = field(default_factory=dict, repr=False)

    _CAMPOS_CONOCIDOS = {
        "votosNulos",
        "votosNulosPorcentaje",
        "votosEnBlanco",
        "votosEnBlancoPorcentaje",
        "votosRecurridosComandoImpugnados",
        "votosRecurridosComandoImpugnadosPorcentaje",
    }

    @classmethod
    def from_json(cls, raw: dict) -> "ValoresOtros":
        return cls(
            votos_nulos=raw["votosNulos"],
            votos_nulos_porcentaje=raw["votosNulosPorcentaje"],
            votos_en_blanco=raw["votosEnBlanco"],
            votos_en_blanco_porcentaje=raw["votosEnBlancoPorcentaje"],
            votos_recurridos_comando_impugnados=raw["votosRecurridosComandoImpugnados"],
            votos_recurridos_comando_impugnados_porcentaje=raw[
                "votosRecurridosComandoImpugnadosPorcentaje"
            ],
            extra=_extra(raw, cls._CAMPOS_CONOCIDOS),
        )


@dataclass
class ResultadoElectoral:
    fecha_totalizacion: str
    estado_recuento: EstadoRecuento
    valores_totalizados_positivos: list[ValorAgrupacion]
    valores_totalizados_otros: ValoresOtros
    consulta: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict, repr=False)

    _CAMPOS_CONOCIDOS = {
        "fechaTotalizacion",
        "estadoRecuento",
        "valoresTotalizadosPositivos",
        "valoresTotalizadosOtros",
    }

    @classmethod
    def from_json(cls, raw: dict, consulta: dict | None = None) -> "ResultadoElectoral":
        return cls(
            fecha_totalizacion=raw["fechaTotalizacion"],
            estado_recuento=EstadoRecuento.from_json(raw["estadoRecuento"]),
            valores_totalizados_positivos=[
                ValorAgrupacion.from_json(v) for v in raw["valoresTotalizadosPositivos"]
            ],
            valores_totalizados_otros=ValoresOtros.from_json(raw["valoresTotalizadosOtros"]),
            consulta=consulta or {},
            extra=_extra(raw, cls._CAMPOS_CONOCIDOS),
        )

    @property
    def ganador(self) -> ValorAgrupacion | None:
        if not self.valores_totalizados_positivos:
            return None
        return max(self.valores_totalizados_positivos, key=lambda v: v.votos)

    @property
    def total_votos_positivos(self) -> int:
        return sum(v.votos for v in self.valores_totalizados_positivos)

    @property
    def es_mesa(self) -> bool:
        """True si esta consulta apunta a una mesa puntual (viene con `mesaId`)."""
        return self.consulta.get("mesa_id") is not None
