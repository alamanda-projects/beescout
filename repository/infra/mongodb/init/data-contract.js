db = db.getSiblingDB("dgrdb");

db.dgr.insertOne({
  standard_version: "0.1.0",
  contract_number: "3oxinjpVbBefh",
  metadata: {
    version: "1.0.1",
    type: "CSV",
    name: "customer list",
    owner: "marketing division",
    consumption_mode: "Analytical",
    description: {
      purpose: "This dataset will be used to combine with others dataset for specific use case.",
      usage: "private"
    },
    consumer: [
      {
        name: "penjualan",
        use_case: "combine the dataset to transactional data, the results are obtained to find out a person's purchasing history."
      },
      {
        name: "analytic-engineer",
        use_case: "enrich the customer datasets."
      }
    ],
    stakeholders: [
      {
        name: "John Doe",
        email: "john.doe@mail.me",
        role: "owner",
        date_in: "2023-08-13T09:07:54.000Z",
        date_out: null
      },
      {
        name: "Jean Doe",
        email: "jean.doe@mail.me",
        role: "consumer",
        date_in: "2023-08-13T09:07:54.000Z",
        date_out: "2023-09-16T09:07:54.000Z"
      },
      {
        name: "Fulanah",
        email: "fulanah@mail.me",
        role: "consumer",
        date_in: "2023-09-16T09:07:54.000Z",
        date_out: null
      }
    ],
    quality: [
      {
        code: "count_check",
        description: "ensure the dataset is in accordance with the agreed volume range",
        dimension: "completeness",
        impact: "operational",
        custom_properties: [
          {
            property: "field_condition",
            value: "is_nullable=false"
          },
          {
            property: "field_condition",
            value: "is_audit=true"
          }
        ]
      },
      {
        code: "distinct_check",
        description: "ensure there is no duplicate data",
        dimension: "completeness",
        impact: "operational",
        custom_properties: [
          {
            property: "field_name",
            value: "uid"
          },
          {
            property: "field_name",
            value: "name"
          },
          {
            property: "field_name",
            value: "join_date"
          }
        ]
      },
      {
        code: "pii_check",
        description: "ensure PII was masking",
        dimension: "completeness",
        impact: "operational",
        custom_properties: [
          {
            property: "field_name",
            value: "name"
          }
        ]
      }
    ],
    sla: {
      availability_start: 6,
      availability_end: 18,
      availability_unit: "h",
      frequency: 4,
      frequency_unit: "h",
      frequency_cron: "0 0/6 * * *",
      retention: 1,
      retention_unit: "y",
      effective_date: "2023-08-13T09:07:54.000Z",
      end_of_contract: "2025-08-13T09:07:54.000Z"
    }
  },
  model: [
    {
      column: "uid",
      business_name: "User ID",
      logical_type: "string",
      physical_type: "varchar(36)",
      is_primary: true,
      is_nullable: false,
      is_partition: true,
      is_clustered: false,
      is_pii: true,
      is_audit: false,
      is_mandatory: true,
      description: "User identifier column, this column is required and must be unique value",
      quality: [
        {
          code: "null_check",
          description: "ensure that the column rows are complete according to the expected number of rows",
          dimension: "completeness",
          impact: "operational",
          custom_properties: [
            {
              property: "compare_to",
              value: "total dataset row"
            },
            {
              property: "comparison_type",
              value: "equal to"
            }
          ]
        },
        {
          code: "format_check",
          description: "ensure the value does not exceed the agreed nomenclature limits",
          dimension: "validity",
          impact: "operational",
          custom_properties: [
            {
              property: "length",
              value: 36
            }
          ]
        }
      ],
      sample_value: [
        "4d60b9fe-3311-4edb-986a-5f93c79c61ac",
        "386acf0e-5ed2-48d4-99b5-af5683207bd2"
      ],
      tags: [
        "tag1",
        "tag2"
      ]
    },
    {
      column: "name",
      business_name: "Full Name",
      logical_type: "string",
      physical_type: "varchar(100)",
      is_primary: false,
      is_nullable: false,
      is_partition: true,
      is_clustered: false,
      is_pii: true,
      is_audit: false,
      is_mandatory: true,
      description: "Column that represent the user full name",
      quality: [
        {
          code: "null_check",
          description: "ensure that the column rows are complete according to the expected number of rows",
          dimension: "completeness",
          impact: "operational",
          custom_properties: [
            {
              property: "compare_to",
              value: "total dataset row"
            },
            {
              property: "comparison_type",
              value: "equal to"
            }
          ]
        },
        {
          code: "string_check",
          description: "ensure column values only contain strings",
          dimension: "accuracy",
          impact: "operational",
          custom_properties: [
            {
              property: "contains only",
              value: "alphabet"
            }
          ]
        }
      ],
      sample_value: [
        "Fulan Bin Fulan",
        "Agus",
        "Budi Dwihartoyo"
      ],
      tags: [
        "tag1",
        "tag2"
      ]
    },
    {
      column: "join_date",
      business_name: "Join Date",
      logical_type: "date",
      physical_type: "date",
      is_primary: false,
      is_nullable: false,
      is_partition: true,
      is_clustered: false,
      is_pii: true,
      is_audit: false,
      is_mandatory: false,
      description: "Column that represent when the user join",
      quality: [
        {
          code: "null_check",
          description: "ensure that the column rows are complete according to the expected number of rows",
          dimension: "completeness",
          impact: "operational",
          custom_properties: [
            {
              property: "compare_to",
              value: "total dataset row"
            },
            {
              property: "comparison_type",
              value: "equal to"
            }
          ]
        },
        {
          code: "date_range_check",
          description: "ensure the value does not exceed the agreed limit",
          dimension: "accuracy",
          impact: "operational",
          custom_properties: [
            {
              property: "min_date",
              value: "1940-01-01T00:00:00.000Z"
            },
            {
              property: "max_date",
              value: "today"
            }
          ]
        }
      ],
      sample_value: [
        "1990-03-07T00:00:00.000Z",
        "1995-09-13T00:00:00.000Z"
      ],
      tags: [
        "tag1",
        "tag2"
      ]
    },
    {
      column: "updated_at",
      business_name: "Updated At",
      logical_type: "datetime",
      physical_type: "datetime",
      is_primary: false,
      is_nullable: false,
      is_partition: true,
      is_clustered: false,
      is_pii: false,
      is_audit: true,
      is_mandatory: true,
      description: "column that explains the last time the row was updated",
      quality: [
        {
          code: "null_check",
          description: "ensure that the column rows are complete according to the expected number of rows",
          dimension: "completeness",
          impact: "operational",
          custom_properties: [
            {
              property: "compare_to",
              value: "total dataset row"
            },
            {
              property: "comparison_type",
              value: "equal to"
            }
          ]
        },
        {
          code: "date_range_check",
          description: "ensure the value does not exceed the agreed limit",
          dimension: "accuracy",
          impact: "operational",
          custom_properties: [
            {
              property: "max_date",
              value: "today"
            }
          ]
        }
      ],
      sample_value: [
        "2023-08-13T09:07:54.000Z"
      ],
      tags: [
        "tag1",
        "tag2"
      ]
    },
    {
      column: "updated_by",
      business_name: "Updated By",
      logical_type: "datetime",
      physical_type: "datetime",
      is_primary: false,
      is_nullable: false,
      is_partition: true,
      is_clustered: false,
      is_pii: false,
      is_audit: true,
      is_mandatory: true,
      description: "column that explains who was updated the row",
      quality: [
        {
          code: "null_check",
          description: "ensure that the column rows are complete according to the expected number of rows",
          dimension: "completeness",
          impact: "operational",
          custom_properties: [
            {
              property: "compare_to",
              value: "total dataset row"
            },
            {
              property: "comparison_type",
              value: "equal to"
            }
          ]
        },
        {
          code: "string_check",
          description: "ensure column values only contain strings",
          dimension: "accuracy",
          impact: "operational",
          custom_properties: [
            {
              property: "contains only",
              value: "alphabet"
            }
          ]
        }
      ],
      sample_value: [
        "Fulan Bin Fulan",
        "Agus",
        "Budi Dwihartoyo"
      ],
      tags: [
        "tag1",
        "tag2"
      ]
    },
    {
      column: "created_at",
      business_name: "Created At",
      logical_type: "datetime",
      physical_type: "datetime",
      is_primary: false,
      is_nullable: false,
      is_partition: true,
      is_clustered: false,
      is_pii: false,
      is_audit: true,
      is_mandatory: true,
      description: "column that explains the last time the row was created",
      quality: [
        {
          code: "null_check",
          description: "ensure that the column rows are complete according to the expected number of rows",
          dimension: "completeness",
          impact: "operational",
          custom_properties: [
            {
              property: "compare_to",
              value: "total dataset row"
            },
            {
              property: "comparison_type",
              value: "equal to"
            }
          ]
        },
        {
          code: "date_range_check",
          description: "ensure the value does not exceed the agreed limit",
          dimension: "accuracy",
          impact: "operational",
          custom_properties: [
            {
              property: "min_date",
              value: "1969-12-31T17:00:00.000Z"
            }
          ]
        }
      ],
      sample_value: [
        "2023-08-13T09:07:54.000Z"
      ],
      tags: [
        "tag1",
        "tag2"
      ]
    },
    {
      column: "created_by",
      business_name: "Created By",
      logical_type: "datetime",
      physical_type: "datetime",
      is_primary: false,
      is_nullable: false,
      is_partition: true,
      is_clustered: false,
      is_pii: false,
      is_audit: true,
      is_mandatory: true,
      description: "column that explains who was created the row",
      quality: [
        {
          code: "null_check",
          description: "ensure that the column rows are complete according to the expected number of rows",
          dimension: "completeness",
          impact: "operational",
          custom_properties: [
            {
              property: "compare_to",
              value: "total dataset row"
            },
            {
              property: "comparison_type",
              value: "equal to"
            }
          ]
        },
        {
          code: "string_check",
          description: "ensure column values only contain strings",
          dimension: "accuracy",
          impact: "operational",
          custom_properties: [
            {
              property: "contains only",
              value: "alphabet"
            }
          ]
        }
      ],
      sample_value: [
        "Fulan Bin Fulan",
        "Agus",
        "Budi Dwihartoyo"
      ],
      tags: [
        "tag1",
        "tag2"
      ]
    },
    {
      column: "deleted_at",
      business_name: "Deleted At",
      logical_type: "datetime",
      physical_type: "datetime",
      is_primary: false,
      is_nullable: false,
      is_partition: true,
      is_clustered: false,
      is_pii: false,
      is_audit: true,
      is_mandatory: false,
      description: "column that explains the last time the row was deleted",
      quality: [
        {
          code: "null_check",
          description: "ensure that the column rows are complete according to the expected number of rows",
          dimension: "completeness",
          impact: "operational",
          custom_properties: [
            {
              property: "compare_to",
              value: "total dataset row"
            },
            {
              property: "comparison_type",
              value: "less than"
            }
          ]
        },
        {
          code: "date_range_check",
          description: "ensure the value does not exceed the agreed limit",
          dimension: "accuracy",
          impact: "operational",
          custom_properties: [
            {
              property: "min_date",
              value: "1969-12-31T17:00:00.000Z"
            }
          ]
        }
      ],
      sample_value: [
        "2023-08-13T09:07:54.000Z"
      ],
      tags: [
        "tag1",
        "tag2"
      ]
    },
    {
      column: "deleted_by",
      business_name: "Deleted By",
      logical_type: "datetime",
      physical_type: "datetime",
      is_primary: false,
      is_nullable: false,
      is_partition: true,
      is_clustered: false,
      is_pii: false,
      is_audit: true,
      is_mandatory: false,
      description: "column that explains who was deleted the row",
      quality: [
        {
          code: "null_check",
          description: "ensure that the column rows are complete according to the expected number of rows",
          dimension: "completeness",
          impact: "operational",
          custom_properties: [
            {
              property: "compare_to",
              value: "total dataset row"
            },
            {
              property: "comparison_type",
              value: "equal to"
            }
          ]
        },
        {
          code: "string_check",
          description: "ensure column values only contain strings",
          dimension: "accuracy",
          impact: "operational",
          custom_properties: [
            {
              property: "contains only",
              value: "alphabet"
            }
          ]
        }
      ],
      sample_value: [
        "Fulan Bin Fulan",
        "Agus",
        "Budi Dwihartoyo"
      ],
      tags: [
        "tag1",
        "tag2"
      ]
    }
  ],
  ports: [
    {
      object: "source",
      properties: [
        {
          property: "type",
          value: "s3"
        },
        {
          property: "location",
          value: "s3://path/to/object"
        }
      ]
    },
    {
      object: "destination",
      properties: [
        {
          property: "type",
          value: "bigquery"
        },
        {
          property: "project",
          value: "project_name"
        },
        {
          property: "dataset",
          value: "dataset_name"
        }
      ]
    }
  ],
  examples: {
    type: "csv",
    data: "uid;name;join_date;updated_at;updated_by;created_at;created_by;deleted_at;deleted_by\n4d60b9fe-3311-4edb-986a-5f93c79c61ac;Hani Perkasa;2022-01-08;2023-08-13T16:07:54+07:00;admin;2023-08-13T16:07:54+07:00;admin;;\n386acf0e-5ed2-48d4-99b5-af5683207bd2;H4ni Nurchairil;2020-03-17;2023-08-13T16:07:54+07:00;;2023-08-13T16:07:54+07:00;admin;2023-08-14T16:07:54+07:00;admin\necc4992b-10fc-4621-9378-999a78a00804;Fulanah;;2021-08-13T16:07:54+07:00;admin;2023-08-13T16:07:54+07:00;admin;;"
  }
});