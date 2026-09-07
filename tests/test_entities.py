from transcriptor_notarial.core import entities


def test_detecta_correo():
    resultado = entities.detectar_entidades("Contacto: juan.perez@example.com para dudas.")
    tipos = [c.tipo for c in resultado]
    assert entities.TipoEntidad.CORREO in tipos


def test_detecta_codigo_postal():
    resultado = entities.detectar_entidades("Domicilio en Colonia Centro, CP 44100.")
    tipos = [c.tipo for c in resultado]
    assert entities.TipoEntidad.CODIGO_POSTAL in tipos


def test_detecta_fecha_en_letra():
    resultado = entities.detectar_entidades("siendo el dia 15 de marzo de 2024 se firma.")
    tipos = [c.tipo for c in resultado]
    assert entities.TipoEntidad.FECHA in tipos


def test_detecta_numero_de_escritura():
    resultado = entities.detectar_entidades("ESCRITURA NUMERO 12345 otorgada ante el notario.")
    tipos = [c.tipo for c in resultado]
    assert entities.TipoEntidad.NUMERO_ESCRITURA in tipos


def test_detecta_moneda():
    resultado = entities.detectar_entidades("por la cantidad de $50,000.00 pagaderos de contado.")
    tipos = [c.tipo for c in resultado]
    assert entities.TipoEntidad.MONEDA in tipos


def test_detecta_superficie():
    resultado = entities.detectar_entidades("con una superficie de 120.50 m2 de terreno.")
    tipos = [c.tipo for c in resultado]
    assert entities.TipoEntidad.SUPERFICIE in tipos


def test_detecta_nombre_completo():
    resultado = entities.detectar_entidades("comparece el señor Juan Antonio Perez Gonzalez.")
    tipos = [c.tipo for c in resultado]
    assert entities.TipoEntidad.NOMBRE_COMPLETO in tipos


def test_no_modifica_el_texto_original():
    texto = "CP 44100 y $1,000.00 pesos"
    entities.detectar_entidades(texto)
    assert texto == "CP 44100 y $1,000.00 pesos"


def test_coincidencias_no_se_solapan():
    resultado = entities.detectar_entidades(
        "ESCRITURA NUMERO 12345 con folio 6789 y CP 44100 en fecha 15 de marzo de 2024."
    )
    rangos = [(c.inicio, c.fin) for c in resultado]
    rangos.sort()
    for (i1, f1), (i2, f2) in zip(rangos, rangos[1:]):
        assert f1 <= i2, f"Solapamiento entre rangos {(i1, f1)} y {(i2, f2)}"


def test_verificar_consistencia_advierte_numero_y_letra():
    texto = "$50,000.00 (cincuenta mil pesos 00/100 M.N.)"
    advertencias = entities.verificar_consistencia_cantidades(texto)
    assert len(advertencias) == 1


def test_verificar_consistencia_sin_advertencia_si_falta_uno():
    texto = "solo texto sin cantidades relevantes aqui"
    advertencias = entities.verificar_consistencia_cantidades(texto)
    assert advertencias == []
