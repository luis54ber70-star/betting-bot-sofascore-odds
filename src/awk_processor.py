import subprocess
import os
from datetime import datetime

def run_awk_on_logs(awk_script: str, input_text: str = None, input_file: str = None) -> str:
    """
    Ejecuta un script AWK sobre texto o archivo.
    """
    if input_file and os.path.exists(input_file):
        cmd = ["awk", awk_script, input_file]
    elif input_text:
        cmd = ["awk", awk_script]
        input_data = input_text.encode()
    else:
        return "Error: Debes proporcionar input_text o input_file"

    try:
        result = subprocess.run(
            cmd,
            input=input_data if 'input_data' in locals() else None,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"Error AWK: {result.stderr}")
            return result.stderr
        return result.stdout.strip()
    except Exception as e:
        return f"Excepción al ejecutar AWK: {e}"


def analyze_scanner_logs(logs: str):
    """Ejemplo de análisis avanzado de logs del Live Scanner con AWK"""
    
    awk_script = r'''
    BEGIN {
        picks = 0;
        total_edge = 0;
        max_edge = 0;
        strong_picks = 0;
    }
    /VALUE PICK/ {
        picks++;
        print $0;
    }
    /Edge: \+([0-9.]+)/ {
        match($0, /Edge: \+([0-9.]+)/, arr);
        edge = arr[1] + 0;
        total_edge += edge;
        if (edge > max_edge) max_edge = edge;
        if (edge > 0.10) strong_picks++;
    }
    END {
        if (picks > 0) {
            avg_edge = total_edge / picks;
            print "\n=== RESUMEN AWK ===";
            print "Picks encontrados: " picks;
            print "Edge promedio:    " avg_edge "%";
            print "Edge máximo:      " max_edge "%";
            print "Picks fuertes (>10%): " strong_picks;
            print "Hora de análisis: " strftime("%Y-%m-%d %H:%M:%S");
        } else {
            print "No se encontraron VALUE PICKs en esta ejecución.";
        }
    }
    '''

    result = run_awk_on_logs(awk_script, input_text=logs)
    return result


# Función para integrar directamente en live_scanner
def process_with_awk(log_output: str):
    summary = analyze_scanner_logs(log_output)
    print("\n" + "="*50)
    print("RESUMEN AWK PROCESADO")
    print("="*50)
    print(summary)
    
    # Opcional: enviar resumen por Telegram
    from src.notifier import send_telegram
    if "Picks encontrados" in summary:
        send_telegram(f"<b>📊 Resumen AWK</b>\n\n{summary}")
    
    return summary
