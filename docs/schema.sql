CREATE TABLE departments (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    geometry_uri TEXT,
    area_km2 REAL
);

CREATE TABLE weather_runs (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    model TEXT NOT NULL,
    run_time TIMESTAMP NOT NULL,
    horizon_hours INTEGER NOT NULL,
    available_at TIMESTAMP NOT NULL,
    raw_uri TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weather_grid_values (
    run_id TEXT NOT NULL REFERENCES weather_runs(id),
    valid_time TIMESTAMP NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    variable TEXT NOT NULL,
    value REAL NOT NULL
);

CREATE TABLE department_weather_features (
    department_code TEXT NOT NULL REFERENCES departments(code),
    target_date DATE NOT NULL,
    horizon INTEGER NOT NULL CHECK (horizon BETWEEN 0 AND 7),
    available_at TIMESTAMP NOT NULL,
    source_run_id TEXT REFERENCES weather_runs(id),
    features_json TEXT NOT NULL,
    PRIMARY KEY (department_code, target_date, horizon, available_at)
);

CREATE TABLE fire_events (
    id TEXT PRIMARY KEY,
    event_date DATE NOT NULL,
    commune_code TEXT,
    department_code TEXT NOT NULL REFERENCES departments(code),
    burned_area_ha REAL,
    source TEXT NOT NULL,
    raw_uri TEXT
);

CREATE TABLE official_vigilance (
    department_code TEXT NOT NULL REFERENCES departments(code),
    target_date DATE NOT NULL,
    phenomenon TEXT NOT NULL,
    level INTEGER NOT NULL CHECK (level BETWEEN 0 AND 3),
    issued_at TIMESTAMP NOT NULL,
    source TEXT NOT NULL,
    raw_uri TEXT,
    PRIMARY KEY (department_code, target_date, phenomenon, issued_at)
);

CREATE TABLE model_versions (
    version TEXT PRIMARY KEY,
    algorithm TEXT NOT NULL,
    artifact_uri TEXT NOT NULL,
    thresholds_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('candidate', 'production', 'rejected', 'archived')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    promoted_at TIMESTAMP
);

CREATE TABLE predictions (
    id TEXT PRIMARY KEY,
    model_version TEXT NOT NULL REFERENCES model_versions(version),
    department_code TEXT NOT NULL REFERENCES departments(code),
    target_date DATE NOT NULL,
    horizon INTEGER NOT NULL CHECK (horizon BETWEEN 0 AND 7),
    available_at TIMESTAMP NOT NULL,
    score REAL NOT NULL CHECK (score BETWEEN 0 AND 100),
    level INTEGER NOT NULL CHECK (level BETWEEN 0 AND 3),
    probabilities_json TEXT NOT NULL,
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE prediction_explanations (
    prediction_id TEXT PRIMARY KEY REFERENCES predictions(id),
    method TEXT NOT NULL,
    factors_json TEXT NOT NULL
);

CREATE TABLE backtest_runs (
    id TEXT PRIMARY KEY,
    model_version TEXT NOT NULL REFERENCES model_versions(version),
    train_start DATE NOT NULL,
    train_end DATE NOT NULL,
    validation_start DATE NOT NULL,
    validation_end DATE NOT NULL,
    test_start DATE NOT NULL,
    test_end DATE NOT NULL,
    metrics_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
