package mohawksdk

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

func TestBridgeContractMetadata(t *testing.T) {
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("cannot get caller path")
	}
	versionPath := filepath.Clean(filepath.Join(filepath.Dir(file), "..", "..", "..", "bridge", "bridge_contract.version.json"))
	raw, err := os.ReadFile(versionPath)
	if err != nil {
		t.Fatalf("read version file: %v", err)
	}
	var version map[string]string
	if err := json.Unmarshal(raw, &version); err != nil {
		t.Fatalf("parse version file: %v", err)
	}

	if BridgeContractName != version["contract"] {
		t.Fatalf("contract name mismatch: %q != %q", BridgeContractName, version["contract"])
	}
	if BridgeContractSchemaVersion != version["schema_version"] {
		t.Fatalf("schema version mismatch: %q != %q", BridgeContractSchemaVersion, version["schema_version"])
	}
	if BridgeContractManifestVersion != version["manifest_version"] {
		t.Fatalf("manifest version mismatch: %q != %q", BridgeContractManifestVersion, version["manifest_version"])
	}
	if len(BridgeContractSchemaSHA256) != 64 {
		t.Fatalf("unexpected schema hash length: %d", len(BridgeContractSchemaSHA256))
	}
}
