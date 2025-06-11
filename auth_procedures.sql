-- Stored procedures for authentication
-- DBMS: SQL Server

-- Procedure to register a new user
CREATE PROCEDURE [usp_register_user]
    @TenantId INT,
    @OrganizationId INT = NULL,
    @Username NVARCHAR(100),
    @Email NVARCHAR(255),
    @PasswordHash NVARCHAR(255),
    @DisplayName NVARCHAR(200) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO [users] (
        [tenant_id],
        [organization_id],
        [username],
        [email],
        [password],
        [display_name],
        [created_at]
    ) VALUES (
        @TenantId,
        @OrganizationId,
        @Username,
        @Email,
        @PasswordHash,
        @DisplayName,
        GETDATE()
    );

    SELECT SCOPE_IDENTITY() AS [user_id];
END
GO

-- Procedure to authenticate a user
CREATE PROCEDURE [usp_authenticate_user]
    @Username NVARCHAR(100),
    @PasswordHash NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT [user_id], [tenant_id], [username], [email], [status]
    FROM [users]
    WHERE [username] = @Username
      AND [password] = @PasswordHash
      AND [deleted_at] IS NULL;
END
GO

-- Procedure to generate a password reset token
CREATE PROCEDURE [usp_set_password_reset_token]
    @UserId INT,
    @Token NVARCHAR(100),
    @ExpiresAt DATETIME
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE [users]
    SET [password_reset_token] = @Token,
        [password_reset_expires] = @ExpiresAt
    WHERE [user_id] = @UserId;
END
GO