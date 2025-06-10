db = db.getSiblingDB("dgrdb");

// Optional: insert user into collection
db.dgrusr.insertOne({
  username: "root",
  password: "$2b$12$BRd2gyH3NU2OMiv.1G3peeiardJhieieaneI1mqwP8kB6oH/vnrtS",
  name: "Iam Root",
  group_access: "root",
  data_domain: "root",
  type: "user",
  is_active: true,
  created_at: new Date()
});