*** Settings ***
Library    SeleniumLibrary
Library    helper.py
Suite Teardown    Close All Browsers

*** Variables ***
${REPORT_FILE}        ${CURDIR}/report.html
${PARQUET_FOLDER}     C:/Work/Trainings/DQ Automation/dqe-automation/parquet_data/facility_type_avg_time_spent_per_visit_date
${FILTER_DATE}        2026-03-29

*** Test Cases ***
Compare HTML Table With Parquet Data
    [Documentation]    Verify that HTML report table matches Parquet dataset
    [Tags]    data-validation
    
    # Step 1: Open HTML report
    Open Browser    file:///${REPORT_FILE}    chrome
    Sleep    2s    # Wait for page to load
    
    # Step 2: Locate the HTML table
    ${table_element}=    Get WebElement    css:g.table
    
    # Step 3: Read table data into DataFrame
    ${html_df}=    Read Html Table To Dataframe    ${table_element}
    Log    HTML DataFrame loaded: ${html_df}
    
    # Step 4: Read Parquet data with optional filtering
    ${parquet_df}=    Read Parquet Data    ${PARQUET_FOLDER}    ${FILTER_DATE}
    Log    Parquet DataFrame loaded: ${parquet_df}
    
    # Step 5: Compare DataFrames
    ${comparison_result}=    Compare Dataframes    ${html_df}    ${parquet_df}
    
    # Step 6: Assert match and report differences
    Log    ${comparison_result}[differences]
    Should Be True    ${comparison_result}[match]    ${comparison_result}[differences]