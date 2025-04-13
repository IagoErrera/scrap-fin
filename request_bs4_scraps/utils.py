from datetime import timezone, timedelta, datetime

def format_date_g1(date_str):
    tz = timezone(timedelta(hours=-3))

    iso = datetime.strptime(date_str, "%d/%m/%Y").replace(hour=0, minute=0, second=0, tzinfo=tz).isoformat()
    iso = iso.replace("-03:00", "-0300")  # Remove ":" do offset
    iso = iso.replace(":", "%3A")  # Codifica os ":" do horário
    return iso

def format_date_folha(date_str):
    return date_str.replace("/", "%2F") 

def estadao_date_to_iso(data_hora_str):
    data_str, hora_str = data_hora_str.split(" | ")
    
    dia, mes, ano = map(int, data_str.split("/"))
    
    hora, minuto = map(int, hora_str.replace("h", ":").split(":"))
    
    data_hora = datetime(ano, mes, dia, hora, minuto)
    
    return data_hora.isoformat()
