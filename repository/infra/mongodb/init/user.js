db = db.getSiblingDB("dgrdb");

// Initial root users are created through the /setup endpoint.
// Keeping this init script as a no-op ensures a fresh install can use the web
// setup flow instead of being locked by a pre-seeded default root account.
