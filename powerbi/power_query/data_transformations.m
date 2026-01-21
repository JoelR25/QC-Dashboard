// Power Query M Script for Control Tower Data Model
// Import and transform data from Databricks exports for Power BI Control Tower Dashboard

// =====================================================================
// FACT TABLE: Gold Sales Data
// =====================================================================

let
    Source = Csv.Document(File.Contents("C:\Data\control_tower_gold.csv"),[Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"Brand", type text}, 
        {"Category", type text}, 
        {"Region", type text}, 
        {"Week_End", type date}, 
        {"Total_Sales", type number}, 
        {"Total_Units", Int64.Type}, 
        {"Transaction_Count", Int64.Type}, 
        {"Avg_Unit_Price", type number}, 
        {"Batch_ID", type text}
    }),
    #"Renamed Columns" = Table.RenameColumns(#"Changed Type",{
        {"Week_End", "Date"},
        {"Total_Sales", "Sales Amount"},
        {"Total_Units", "Units Sold"}
    }),
    #"Added Date Key" = Table.AddColumn(#"Renamed Columns", "DateKey", each Date.ToText([Date], "yyyyMMdd")),
    #"Filtered Rows" = Table.SelectRows(#"Added Date Key", each [Sales Amount] <> null and [Sales Amount] > 0)
in
    #"Filtered Rows"

// =====================================================================
// FACT TABLE: Quarantine Data
// =====================================================================

let
    Source = Csv.Document(File.Contents("C:\Data\control_tower_quarantine.csv"),[Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"UPC", type text}, 
        {"Store_ID", type text}, 
        {"Sales_Dollars", type number}, 
        {"Units_Sold", Int64.Type}, 
        {"Error_Details", type text}, 
        {"Week_End", type date}, 
        {"Quarantine_Timestamp", type datetime}
    }),
    #"Split Error Details" = Table.SplitColumn(#"Changed Type", "Error_Details", 
        Splitter.SplitTextByDelimiter(";", QuoteStyle.Csv), 
        {"Error_1", "Error_2", "Error_3", "Error_4"}),
    #"Extract Error Type" = Table.AddColumn(#"Split Error Details", "Primary_Error_Type", 
        each 
            let
                error1 = [Error_1],
                parts = Text.Split(error1, "|")
            in
                if List.Count(parts) >= 3 then parts{0} else "UNKNOWN"),
    #"Extract Severity" = Table.AddColumn(#"Extract Error Type", "Severity", 
        each 
            let
                error1 = [Error_1],
                parts = Text.Split(error1, "|")
            in
                if List.Count(parts) >= 3 then parts{1} else "UNKNOWN"),
    #"Extract Description" = Table.AddColumn(#"Extract Severity", "Error_Description", 
        each 
            let
                error1 = [Error_1],
                parts = Text.Split(error1, "|")
            in
                if List.Count(parts) >= 3 then parts{2} else "Unknown Error"),
    #"Removed Temp Columns" = Table.RemoveColumns(#"Extract Description",{"Error_1", "Error_2", "Error_3", "Error_4"}),
    #"Renamed Columns" = Table.RenameColumns(#"Removed Temp Columns",{
        {"Week_End", "Date"},
        {"Sales_Dollars", "Quarantined_Sales"},
        {"Units_Sold", "Quarantined_Units"}
    }),
    #"Added Date Key" = Table.AddColumn(#"Renamed Columns", "DateKey", each Date.ToText([Date], "yyyyMMdd")),
    #"Replaced Null Sales" = Table.ReplaceValue(#"Added Date Key", null, 0, Replacer.ReplaceValue,{"Quarantined_Sales"})
in
    #"Replaced Null Sales"

// =====================================================================
// FACT TABLE: Audit Log
// =====================================================================

let
    Source = Csv.Document(File.Contents("C:\Data\control_tower_audit.csv"),[Delimiter=",", Columns=11, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"batch_id", type text}, 
        {"layer_name", type text}, 
        {"timestamp", type datetime}, 
        {"input_rows", Int64.Type}, 
        {"valid_rows", Int64.Type}, 
        {"quarantine_rows", Int64.Type}, 
        {"trust_score", type number}, 
        {"Bronze_Total", Int64.Type}, 
        {"Silver_Valid", Int64.Type}, 
        {"Silver_Quarantine", Int64.Type}, 
        {"Revenue_At_Risk", type number}
    }),
    #"Extracted Date" = Table.AddColumn(#"Changed Type", "Date", each DateTime.Date([timestamp]), type date),
    #"Added Date Key" = Table.AddColumn(#"Extracted Date", "DateKey", each Date.ToText([Date], "yyyyMMdd"))
in
    #"Added Date Key"

// =====================================================================
// DIMENSION TABLE: Product Master
// =====================================================================

let
    Source = Csv.Document(File.Contents("C:\Data\control_tower_products.csv"),[Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"UPC", type text}, 
        {"Brand", type text}, 
        {"Category", type text}, 
        {"Product_Name", type text}, 
        {"List_Price", type number}, 
        {"Active_Flag", type text}
    }),
    #"Filtered Active" = Table.SelectRows(#"Changed Type", each ([Active_Flag] = "Y"))
in
    #"Filtered Active"

// =====================================================================
// DIMENSION TABLE: Store Master
// =====================================================================

let
    Source = Csv.Document(File.Contents("C:\Data\control_tower_stores.csv"),[Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"Store_ID", type text}, 
        {"Retailer_Name", type text}, 
        {"Region", type text}, 
        {"City", type text}, 
        {"State", type text}, 
        {"Active_Flag", type text}
    }),
    #"Filtered Active" = Table.SelectRows(#"Changed Type", each ([Active_Flag] = "Y"))
in
    #"Filtered Active"

// =====================================================================
// DIMENSION TABLE: Error Code Lookup
// =====================================================================

let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i45WMlTSUTI0VDKK1THX...", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [
        #"Error_Code" = _t, 
        #"Error_Name" = _t, 
        #"Error_Description" = _t, 
        #"Severity" = _t, 
        #"Remediation" = _t
    ]),
    #"Manual Error Codes" = Table.FromRecords({
        [Error_Code = "upc_not_null", Error_Name = "Missing UPC", Error_Description = "UPC must not be null", Severity = "CRITICAL", Remediation = "Investigate source data quality"],
        [Error_Code = "sales_not_null", Error_Name = "Missing Sales", Error_Description = "Sales_Dollars must not be null", Severity = "CRITICAL", Remediation = "Check data extraction process"],
        [Error_Code = "units_not_null", Error_Name = "Missing Units", Error_Description = "Units_Sold must not be null", Severity = "HIGH", Remediation = "Verify transaction completeness"],
        [Error_Code = "upc_in_master", Error_Name = "Orphan UPC", Error_Description = "UPC does not exist in Product Master", Severity = "CRITICAL", Remediation = "Update Product Master or investigate new product launch"],
        [Error_Code = "store_in_master", Error_Name = "Unknown Store", Error_Description = "Store ID not in Store Master", Severity = "CRITICAL", Remediation = "Update Store Master or investigate store closure"],
        [Error_Code = "non_negative_sales", Error_Name = "Negative Sales", Error_Description = "Sales amount is negative", Severity = "HIGH", Remediation = "Review returns processing logic"],
        [Error_Code = "reasonable_price", Error_Name = "Extreme Price", Error_Description = "Unit price exceeds $100", Severity = "MEDIUM", Remediation = "Validate pricing data or investigate luxury items"]
    })
in
    #"Manual Error Codes"

// =====================================================================
// DIMENSION TABLE: Date Dimension
// =====================================================================

let
    StartDate = #date(2024, 1, 1),
    EndDate = #date(2026, 12, 31),
    NumberOfDays = Duration.Days(EndDate - StartDate) + 1,
    Dates = List.Dates(StartDate, NumberOfDays, #duration(1, 0, 0, 0)),
    #"Converted to Table" = Table.FromList(Dates, Splitter.SplitByNothing(), {"Date"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Converted to Table",{{"Date", type date}}),
    #"Added Date Key" = Table.AddColumn(#"Changed Type", "DateKey", each Date.ToText([Date], "yyyyMMdd")),
    #"Added Year" = Table.AddColumn(#"Added Date Key", "Year", each Date.Year([Date]), Int64.Type),
    #"Added Quarter" = Table.AddColumn(#"Added Year", "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date]))),
    #"Added Month" = Table.AddColumn(#"Added Quarter", "Month", each Date.Month([Date]), Int64.Type),
    #"Added Month Name" = Table.AddColumn(#"Added Month", "Month Name", each Date.MonthName([Date])),
    #"Added Week" = Table.AddColumn(#"Added Month Name", "Week", each Date.WeekOfYear([Date]), Int64.Type),
    #"Added Day" = Table.AddColumn(#"Added Week", "Day", each Date.Day([Date]), Int64.Type),
    #"Added Day Name" = Table.AddColumn(#"Added Day", "Day Name", each Date.DayOfWeekName([Date])),
    #"Added Is Weekend" = Table.AddColumn(#"Added Day Name", "Is Weekend", 
        each if Date.DayOfWeek([Date], Day.Monday) >= 5 then "Yes" else "No")
in
    #"Added Is Weekend"

// =====================================================================
// HELPER FUNCTIONS
// =====================================================================

// Function to parse error strings
let
    ParseError = (errorString as text) as record =>
    let
        parts = Text.Split(errorString, "|"),
        result = if List.Count(parts) >= 3 then
            [
                ErrorCode = parts{0},
                Severity = parts{1},
                Description = parts{2}
            ]
        else
            [
                ErrorCode = "UNKNOWN",
                Severity = "UNKNOWN",
                Description = errorString
            ]
    in
        result
in
    ParseError

// Function to calculate trust score
let
    CalculateTrustScore = (validRows as number, totalRows as number) as number =>
    let
        trustScore = if totalRows > 0 then (validRows / totalRows) * 100 else 0
    in
        trustScore
in
    CalculateTrustScore
