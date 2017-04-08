Menus
=====
Online Tests
------------
Child of "Settings" menu, parent menu of all other quiz menus

Exams
-----
Child of "Online Tests" menu, place to create new quizzes

Exam Results
------------
Child of "Online Tests" menu, view results of taken tests

Models / Fields
===============
etq.exam (An exam)
------------------
Fields
^^^^^^
**Name (name)**: The name of the quiz

**Slug (slug)**: url version of the exam name

**Show Correct Answers? (show_correct_questions)**: If you should show the correct answers to all the questions on the quiz

**Questions (questions)**: List of questions in a exam

etq.question (A question in an exam)
------------------------------------------------------
Fields
^^^^^^
**Exam ID (exam_id)**: ID the exam of this question

**Question Render (question_rendered)**: Used for fill in the blank questions, it replaces the {_NUMBER_} with textboxes

**Question Type (question_type)**: the type of exam question

**Multiple Choice Options (question_options)**: Question options for multiple choice type questions

**Fill in the Blank Options (question_options_blank)**: Question options for fill in the blank type questions

**Options (num_options)**: The number of options a multiple choice question has

**Correct Options (num_correct)**: The number of correct options a multiple choice question has

etq.question.option (An multiple choice option for a exam question)
-------------------------------------------------------------------
Fields
^^^^^^
**Question ID (question_id)**: ID the question

**Option (option)**: The human read text of the option

**Correct (correct)**: If this option is correct

etq.question.optionblank (An fill in the blank option for a exam question)
--------------------------------------------------------------------------
Fields
^^^^^^
**Question ID (question_id)**: ID the question

**Blank Answer (answer)**: The answer to the fill in the blank

etq.exam.share (Share your quiz for others)
-------------------------------------------
Fields
^^^^^^
**Exam (exam_id)**: ID the exam you want to share

**Share Option (share_type)**: The way you want to share the quiz

**Existing Contacts (partner_ids)**: List of partners you want to share this quiz with

**Email List (email_list)**: Comma separated list of emails you want to email a link to this quiz

**Email Subject (email_subject)**: The subject of email

**Email Content (email_content)**: The HTML content of email

etq.result (The result of taken quizes)
---------------------------------------
Fields
^^^^^^
**Exam (exam_id)**: ID the exam you want to share

**Results (results)**: The questions in the results

etq.result.question (The result of question)
--------------------------------------------
Fields
^^^^^^
**Result (result_id)**: The ID of the exam result

**Result (result_id)**: The ID of the exam result

**Question (question)**: The ID of the exam question

**Options (question_options)**: The options the user selected during the exam

**Correct (correct)**: If this question was marked as correct

**Question (question_name)**: The human read name of the question, should have used name field...

etq.result.question.option (The value the user gave for this option)
--------------------------------------------------------------------
Fields
^^^^^^
**Question ID (question_id)**: The ID of the question

**Option (option_id)**: The ID of the option

**Option Value (question_options_value)**: The value the user gave for this option