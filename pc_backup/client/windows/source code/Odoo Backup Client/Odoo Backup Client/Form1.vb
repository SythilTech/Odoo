Imports System.IO

Public Class Form1


    Dim apiKey As String = ""
    Dim backup_file_count As Integer = 0
    Dim last_backup_time As DateTime
    Dim systemUrl As String = ""
    Dim backup_change_id As String = ""

    Private Sub BackupDirectoriesButton_Click(sender As Object, e As EventArgs) Handles BackupDirectoriesButton.Click
        FolderBrowserDialog1.ShowDialog()

        If BackupDirectoriesTextBox.Text = "" Then
            BackupDirectoriesTextBox.Text = FolderBrowserDialog1.SelectedPath
        Else
            BackupDirectoriesTextBox.Text += "," + FolderBrowserDialog1.SelectedPath
        End If

    End Sub

    Private Sub Form1_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        Dim credsText = My.Computer.FileSystem.ReadAllText("creds.sec")

        Dim credsDictionary As New Dictionary(Of String, String)

        For Each Line As String In File.ReadLines("Creds.sec")
            credsDictionary.Add(Line.Split("=")(0), Line.Split("=")(1))
        Next

        SystemURLTextBox.Text = credsDictionary("url")
        DatabaseNameTextBox.Text = credsDictionary("db")
        BackupDirectoriesTextBox.Text = credsDictionary("directories")
        apiKey = credsDictionary("key")
        last_backup_time = credsDictionary("last-backup-time")

    End Sub

    Private Sub ManualBackupButton_Click(sender As Object, e As EventArgs) Handles ManualBackupButton.Click
        systemUrl = SystemURLTextBox.Text
        Dim directories As String = BackupDirectoriesTextBox.Text

        Dim computerUsername = My.User.Name
        Dim computerName = My.Computer.Name
        Dim webClient As New System.Net.WebClient

        'Register a change
        backup_change_id = webClient.DownloadString(systemUrl + "/backup/client/register/change?key=" + apiKey + "&computer_username=" + computerUsername + "&computer_name=" + computerName)


        backup_file_count = 0

        'Recursively Backup all files
        For Each backup_directory In directories.Split(",")
            BackUpDir(New DirectoryInfo(backup_directory))
        Next

        MsgBox(backup_file_count.ToString + " Files Backed Up")


    End Sub

    Public Sub BackUpDir(ByVal dirInfo As DirectoryInfo)
        For Each filename In Directory.GetFiles(dirInfo.FullName)
            Dim fileInfo As FileInfo = New FileInfo(filename)
            If fileInfo.LastWriteTimeUtc > last_backup_time Then
                Dim encoded_string As String = Convert.ToBase64String(System.IO.File.ReadAllBytes(filename))

                Dim webClient As New System.Net.WebClient

                Dim reqparm As New Specialized.NameValueCollection
                reqparm.Add("key", apiKey)
                reqparm.Add("change_id", backup_change_id)
                reqparm.Add("file_path", filename)
                reqparm.Add("encoded_string", encoded_string)
                Dim responsebytes = webClient.UploadValues(systemUrl + "/backup/client/file/upload", "POST", reqparm)
                Dim responsebody = (New Text.UTF8Encoding).GetString(responsebytes)

                backup_file_count += 1
            End If
        Next

        'Backup all files in the folders too (recursive)
        For Each dirName In Directory.GetDirectories(dirInfo.FullName)
            BackUpDir(New DirectoryInfo(dirName))
        Next
    End Sub

    Private Sub RestoreButton_Click(sender As Object, e As EventArgs) Handles RestoreButton.Click
        systemUrl = SystemURLTextBox.Text
        Process.Start(systemUrl + "/backup/client/machines")
    End Sub
End Class
