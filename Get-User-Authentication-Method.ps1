# Make sure you're connected with proper permissions
# Connect-MgGraph -Scopes "User.Read.All", "UserAuthenticationMethod.Read.All"

# Get all users
$users = Get-MgUser -All | Select-Object Id, UserPrincipalName

# Loop through each user and get their authentication methods
foreach ($user in $users) {
    Write-Output "User: $($user.UserPrincipalName)"
    
    try {
        # Get all authentication methods for the user
        $authMethods = Get-MgUserAuthenticationMethod -UserId $user.Id
        
        # Display each authentication method
        foreach ($method in $authMethods) {
            $methodType = $method.AdditionalProperties.'@odata.type'
            
            # Format the output based on the method type
            switch -Wildcard ($methodType) {
                "*#microsoft.graph.phoneAuthenticationMethod" {
                    $phoneType = $method.AdditionalProperties.phoneType
                    $phoneNumber = $method.AdditionalProperties.phoneNumber
                    Write-Output "  - Method: Phone ($phoneType) - $phoneNumber"
                }
                "*#microsoft.graph.passwordAuthenticationMethod" {
                    Write-Output "  - Method: Password"
                }
                "*#microsoft.graph.microsoftAuthenticatorAuthenticationMethod" {
                    $displayName = $method.AdditionalProperties.displayName
                    Write-Output "  - Method: Microsoft Authenticator - $displayName"
                }
                "*#microsoft.graph.fido2AuthenticationMethod" {
                    $model = $method.AdditionalProperties.model
                    Write-Output "  - Method: FIDO2 Security Key - $model"
                }
                "*#microsoft.graph.softwareOathAuthenticationMethod" {
                    Write-Output "  - Method: Authenticator App (TOTP)"
                }
                "*#microsoft.graph.emailAuthenticationMethod" {
                    $emailAddress = $method.AdditionalProperties.emailAddress
                    Write-Output "  - Method: Email - $emailAddress"
                }
                "*#microsoft.graph.windowsHelloForBusinessAuthenticationMethod" {
                    $displayName = $method.AdditionalProperties.displayName
                    Write-Output "  - Method: Windows Hello - $displayName"
                }
                Default {
                    Write-Output "  - Method: $methodType"
                }
            }
        }
        
        # Add a blank line for readability
        Write-Output ""
    }
    catch {
        Write-Warning "Error retrieving authentication methods for $($user.UserPrincipalName): $_"
    }
}
