variable "table_map" {
    type = list
    default = [
      {
        index = 0,
        dataset = "dummy_dataset"
        parent_project = "dummy_project"
        tables_file = "glue/json/gbq_tables1.json"
      },
      {
        index = 1,
        dataset = "dummy_dataset"
        parent_project = "dummy_project"
        tables_file = "glue/json/gbq_tables2.json"
      }
    ]
}

