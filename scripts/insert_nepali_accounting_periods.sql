-- SQL script to insert Nepali accounting periods for a fiscal year.
-- Adjust fiscal_year_id, organization_id, and period dates as needed.

INSERT INTO accounting_accountingperiod
    (fiscal_year_id, period_number, name, start_date, end_date, status, is_current, created_at,is_adjustment_period,is_archived)
VALUES
    ('1303879700', 1, 'Shrawan 2081-2082', '2024-07-16', '2024-08-16', 'open', 1, GETDATE(),0,0),
    ('1303879700', 2, 'Bhadra 2081-2082', '2024-08-17', '2024-09-16', 'open', 0, GETDATE(),0,0),
    ('1303879700', 3, 'Ashwin 2081-2082', '2024-09-17', '2024-10-16', 'open', 0, GETDATE(),0,0),
    ('1303879700', 4, 'Kartik 2081-2082', '2024-10-17', '2024-11-15', 'open', 0, GETDATE(),0,0),
    ('1303879700', 5, 'Mangsir 2081-2082', '2024-11-16', '2024-12-15', 'open', 0, GETDATE(),0,0),
    ('1303879700', 6, 'Poush 2081-2082', '2024-12-16', '2025-01-14', 'open', 0, GETDATE(),0,0),
    ('1303879700', 7, 'Magh 2081-2082', '2025-01-15', '2025-02-13', 'open', 0, GETDATE(),0,0),
    ('1303879700', 8, 'Falgun 2081-2082', '2025-02-14', '2025-03-15', 'open', 0, GETDATE(),0,0),
    ('1303879700', 9, 'Chaitra 2081-2082', '2025-03-16', '2025-04-14', 'open', 0, GETDATE(),0,0),
    ('1303879700', 10, 'Baisakh 2081-2082', '2025-04-15', '2025-05-15', 'open', 0, GETDATE(),0,0),
    ('1303879700', 11, 'Jestha 2081-2082', '2025-05-16', '2025-06-15', 'open', 0, GETDATE(),0,0),
    ('1303879700', 12, 'Asar 2081-2082', '2025-06-16', '2025-07-16', 'open', 0, GETDATE(),0,0);
