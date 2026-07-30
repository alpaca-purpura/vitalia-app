// handlers_regen.go — regen on-demand de los índices cap↔código (2026-06-11).
//
// El tab Drift/Functionality lee `_code-index.json` + `_bidirectional-validation.json`
// PRE-GENERADOS (los regenera el pre-commit al tocar caps/headers). Entre edición
// y commit el cockpit muestra el índice viejo. Este endpoint cierra esa ventana:
// shellea los scripts python CANÓNICOS del workspace (un solo SSoT — NUNCA
// reimplementar el resolver en Go: un mirror driftearía).
//
// Si el workspace no trae los scripts (proyecto cliente sin ese tooling), el
// endpoint responde hint honesto en vez de fallar.
package main

import (
	"encoding/json"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

var regenMu sync.Mutex

// pythonBin: venv del workspace primero (resolución de deps del repo), python3 fallback.
func pythonBin(root string) string {
	venv := filepath.Join(root, ".venv", "bin", "python")
	if st, err := os.Stat(venv); err == nil && !st.IsDir() {
		return venv
	}
	return "python3"
}

func handleCapRegen(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Sistema string `json:"sistema"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeError(w, 400, "body JSON inválido", nil)
		return
	}
	if !containsStr(getSistemas(), body.Sistema) {
		writeError(w, 400, "sistema desconocido: "+body.Sistema, nil)
		return
	}

	root, err := getWorkspaceRoot()
	if err != nil {
		writeError(w, 500, "workspace root no resuelto: "+err.Error(), nil)
		return
	}

	scripts := []string{
		filepath.Join(root, "scripts", "generate_code_to_cap_index.py"),
		filepath.Join(root, "scripts", "validate_code_cap_bidirectional.py"),
		// computed_status (verified-live/partial/stub por cap) NO corre en pre-commit
		// — sin esto el tab Drift muestra una foto vieja sin que se note.
		filepath.Join(root, "scripts", "compute_capability_status.py"),
	}
	present := scripts[:0]
	for _, sc := range scripts {
		if _, statErr := os.Stat(sc); statErr == nil {
			present = append(present, sc)
		}
	}
	if len(present) == 0 {
		writeJSON(w, 200, map[string]any{
			"ok":   false,
			"hint": "Este workspace no trae los scripts de índices cap↔código — se regeneran solo vía pre-commit (si el kit lo instala).",
		})
		return
	}
	scripts = present

	// Serializar regens (los scripts escriben los mismos JSONs).
	regenMu.Lock()
	defer regenMu.Unlock()

	py := pythonBin(root)
	var outputs []string
	start := time.Now()
	for _, sc := range scripts {
		cmd := exec.Command(py, sc, "--sistema", body.Sistema)
		cmd.Dir = root
		out, runErr := cmd.CombinedOutput()
		tail := string(out)
		if len(tail) > 1200 {
			tail = "…" + tail[len(tail)-1200:]
		}
		outputs = append(outputs, filepath.Base(sc)+":\n"+tail)
		if runErr != nil {
			// El validador sale ≠0 si hay drift — eso NO es error del regen:
			// el reporte se escribió igual y el cockpit lo va a mostrar.
			if strings.Contains(filepath.Base(sc), "validate_code_cap_bidirectional") {
				continue
			}
			writeError(w, 500, "regen falló en "+filepath.Base(sc), map[string]any{
				"output": tail,
			})
			return
		}
	}

	writeJSON(w, 200, map[string]any{
		"ok":          true,
		"sistema":       body.Sistema,
		"duration_ms": time.Since(start).Milliseconds(),
		"output_tail": strings.Join(outputs, "\n---\n"),
	})
}
