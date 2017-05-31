<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()> _
Partial Class Form1
    Inherits System.Windows.Forms.Form

    'Form overrides dispose to clean up the component list.
    <System.Diagnostics.DebuggerNonUserCode()> _
    Protected Overrides Sub Dispose(ByVal disposing As Boolean)
        Try
            If disposing AndAlso components IsNot Nothing Then
                components.Dispose()
            End If
        Finally
            MyBase.Dispose(disposing)
        End Try
    End Sub

    'Required by the Windows Form Designer
    Private components As System.ComponentModel.IContainer

    'NOTE: The following procedure is required by the Windows Form Designer
    'It can be modified using the Windows Form Designer.  
    'Do not modify it using the code editor.
    <System.Diagnostics.DebuggerStepThrough()> _
    Private Sub InitializeComponent()
        Me.SystemURLTextBox = New System.Windows.Forms.TextBox()
        Me.Label1 = New System.Windows.Forms.Label()
        Me.DatabaseNameTextBox = New System.Windows.Forms.TextBox()
        Me.Label2 = New System.Windows.Forms.Label()
        Me.Label3 = New System.Windows.Forms.Label()
        Me.BackupDirectoriesTextBox = New System.Windows.Forms.TextBox()
        Me.BackupDirectoriesButton = New System.Windows.Forms.Button()
        Me.ManualBackupButton = New System.Windows.Forms.Button()
        Me.RestoreButton = New System.Windows.Forms.Button()
        Me.FolderBrowserDialog1 = New System.Windows.Forms.FolderBrowserDialog()
        Me.SuspendLayout()
        '
        'SystemURLTextBox
        '
        Me.SystemURLTextBox.Location = New System.Drawing.Point(120, 29)
        Me.SystemURLTextBox.Name = "SystemURLTextBox"
        Me.SystemURLTextBox.Size = New System.Drawing.Size(100, 20)
        Me.SystemURLTextBox.TabIndex = 0
        '
        'Label1
        '
        Me.Label1.AutoSize = True
        Me.Label1.Location = New System.Drawing.Point(12, 32)
        Me.Label1.Name = "Label1"
        Me.Label1.Size = New System.Drawing.Size(66, 13)
        Me.Label1.TabIndex = 1
        Me.Label1.Text = "System URL"
        '
        'DatabaseNameTextBox
        '
        Me.DatabaseNameTextBox.Location = New System.Drawing.Point(120, 59)
        Me.DatabaseNameTextBox.Name = "DatabaseNameTextBox"
        Me.DatabaseNameTextBox.Size = New System.Drawing.Size(100, 20)
        Me.DatabaseNameTextBox.TabIndex = 2
        '
        'Label2
        '
        Me.Label2.AutoSize = True
        Me.Label2.Location = New System.Drawing.Point(12, 62)
        Me.Label2.Name = "Label2"
        Me.Label2.Size = New System.Drawing.Size(84, 13)
        Me.Label2.TabIndex = 3
        Me.Label2.Text = "Database Name"
        '
        'Label3
        '
        Me.Label3.AutoSize = True
        Me.Label3.Location = New System.Drawing.Point(12, 93)
        Me.Label3.Name = "Label3"
        Me.Label3.Size = New System.Drawing.Size(97, 13)
        Me.Label3.TabIndex = 4
        Me.Label3.Text = "Backup Directories"
        '
        'BackupDirectoriesTextBox
        '
        Me.BackupDirectoriesTextBox.Location = New System.Drawing.Point(120, 90)
        Me.BackupDirectoriesTextBox.Name = "BackupDirectoriesTextBox"
        Me.BackupDirectoriesTextBox.Size = New System.Drawing.Size(100, 20)
        Me.BackupDirectoriesTextBox.TabIndex = 5
        '
        'BackupDirectoriesButton
        '
        Me.BackupDirectoriesButton.Location = New System.Drawing.Point(226, 90)
        Me.BackupDirectoriesButton.Name = "BackupDirectoriesButton"
        Me.BackupDirectoriesButton.Size = New System.Drawing.Size(75, 23)
        Me.BackupDirectoriesButton.TabIndex = 6
        Me.BackupDirectoriesButton.Text = "Browse"
        Me.BackupDirectoriesButton.UseVisualStyleBackColor = True
        '
        'ManualBackupButton
        '
        Me.ManualBackupButton.Location = New System.Drawing.Point(12, 255)
        Me.ManualBackupButton.Name = "ManualBackupButton"
        Me.ManualBackupButton.Size = New System.Drawing.Size(75, 23)
        Me.ManualBackupButton.TabIndex = 7
        Me.ManualBackupButton.Text = "Manual Backup"
        Me.ManualBackupButton.UseVisualStyleBackColor = True
        '
        'RestoreButton
        '
        Me.RestoreButton.Location = New System.Drawing.Point(226, 255)
        Me.RestoreButton.Name = "RestoreButton"
        Me.RestoreButton.Size = New System.Drawing.Size(75, 23)
        Me.RestoreButton.TabIndex = 8
        Me.RestoreButton.Text = "Restore"
        Me.RestoreButton.UseVisualStyleBackColor = True
        '
        'Form1
        '
        Me.AutoScaleDimensions = New System.Drawing.SizeF(6.0!, 13.0!)
        Me.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font
        Me.ClientSize = New System.Drawing.Size(322, 315)
        Me.Controls.Add(Me.RestoreButton)
        Me.Controls.Add(Me.ManualBackupButton)
        Me.Controls.Add(Me.BackupDirectoriesButton)
        Me.Controls.Add(Me.BackupDirectoriesTextBox)
        Me.Controls.Add(Me.Label3)
        Me.Controls.Add(Me.Label2)
        Me.Controls.Add(Me.DatabaseNameTextBox)
        Me.Controls.Add(Me.Label1)
        Me.Controls.Add(Me.SystemURLTextBox)
        Me.Name = "Form1"
        Me.Text = "Form1"
        Me.ResumeLayout(False)
        Me.PerformLayout()

    End Sub

    Friend WithEvents SystemURLTextBox As TextBox
    Friend WithEvents Label1 As Label
    Friend WithEvents DatabaseNameTextBox As TextBox
    Friend WithEvents Label2 As Label
    Friend WithEvents Label3 As Label
    Friend WithEvents BackupDirectoriesTextBox As TextBox
    Friend WithEvents BackupDirectoriesButton As Button
    Friend WithEvents ManualBackupButton As Button
    Friend WithEvents RestoreButton As Button
    Friend WithEvents FolderBrowserDialog1 As FolderBrowserDialog
End Class
