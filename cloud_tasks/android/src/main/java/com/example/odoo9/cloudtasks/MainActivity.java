package com.example.odoo9.cloudtasks;

import android.app.AlertDialog;
import android.content.DialogInterface;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.util.Log;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.Spinner;

import com.android.volley.Request;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonArrayRequest;
import com.android.volley.toolbox.StringRequest;
import com.google.firebase.FirebaseApp;
import com.google.firebase.iid.FirebaseInstanceId;
import com.google.firebase.messaging.FirebaseMessaging;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    String odoo_server_url = "http://10.0.0.33:8069";
    final List<String> listValues = new ArrayList<String>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        //JSON request the task categories
        String tag_json_array = "json_obj_req_task_categories";
        String url = odoo_server_url + "/cloud/task/categories";

        final Spinner spinnerTaskCategories = (Spinner)findViewById(R.id.spinnerTaskCategories);

        final List<String> list;


        list = new ArrayList<String>();

        JsonArrayRequest req = new JsonArrayRequest(url,
                new Response.Listener<JSONArray>() {
                    @Override
                    public void onResponse(JSONArray jsonArray) {
                        Log.d("Log : ","Get Task Category Response");
                        for (int i = 0; i < jsonArray.length(); i++) {
                            JSONObject row = null;
                            try {
                                row = jsonArray.getJSONObject(i);
                                String taskCategoryName = row.getString("name");
                                String taskCategoryID = row.getString("id");
                                Log.d("Log : ", taskCategoryName);
                                list.add(taskCategoryName);
                                listValues.add(taskCategoryID);
                            } catch (JSONException e) {
                                e.printStackTrace();
                            }

                        }

                        ArrayAdapter<String> adapter = new ArrayAdapter<String>(getApplicationContext(),
                                android.R.layout.simple_spinner_item, list);
                        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
                        spinnerTaskCategories.setAdapter(adapter);

                    }
                }, new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {
                Log.d("Log : ","Get Task Category Failure");
            }
        });

        // Adding request to request queue
        AppController.getInstance().addToRequestQueue(req, tag_json_array);

    }

    public void taskCategorySubscribe(View view) {
        Log.d("Log : ","Task Subscribe");

        Spinner spinnerTaskCategories = (Spinner)findViewById(R.id.spinnerTaskCategories);
        String taskCategory = spinnerTaskCategories.getSelectedItem().toString();;
        String id = listValues.get(spinnerTaskCategories.getSelectedItemPosition());

        String taskTopic = "category_" + id;
        Log.d("Log : ",taskTopic);


        FirebaseApp.initializeApp(this);
        String IID_TOKEN = FirebaseInstanceId.getInstance().getToken();
        Log.d("Log : ",IID_TOKEN);
        FirebaseMessaging.getInstance().subscribeToTopic(taskTopic);

        //Show alert that the task has been created
        AlertDialog alertDialog = new AlertDialog.Builder(MainActivity.this).create();
        alertDialog.setTitle("Task Created");
        alertDialog.setMessage("Subscribed to " + taskCategory);
        alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, "OK",
                new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int which) {
                        dialog.dismiss();
                    }
                });
        alertDialog.show();

    }

    public void submitTask(View view) {
        Log.d("Log : ","Submit Task event");

        Spinner spinnerTaskCategories = (Spinner)findViewById(R.id.spinnerTaskCategories);
        String taskCategory = spinnerTaskCategories.getSelectedItem().toString();

        EditText taskSubjectEdit = (EditText)findViewById(R.id.editTaskSubject);
        String taskSubject = taskSubjectEdit.getText().toString();

        EditText taskDescriptionEdit = (EditText)findViewById(R.id.editTaskDescription);
        String taskDescription = taskDescriptionEdit.getText().toString();

        //Execute the create task controller
        String tag_string_req = "json_obj_req_task_create";
        String url = odoo_server_url + "/cloud/task/create?category=" + taskCategory + "&name=" + taskSubject + "&description=" + taskDescription;

        StringRequest strReq = new StringRequest(Request.Method.GET,
                url, new Response.Listener<String>() {

            @Override
            public void onResponse(String response) {
                Log.d("Log : ","Task Create Response");

                //Show alert that the task has been created
                AlertDialog alertDialog = new AlertDialog.Builder(MainActivity.this).create();
                alertDialog.setTitle("Task Created");
                alertDialog.setMessage(response.toString());
                alertDialog.setButton(AlertDialog.BUTTON_NEUTRAL, "OK",
                        new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int which) {
                                dialog.dismiss();
                            }
                        });
                alertDialog.show();


            }
        }, new Response.ErrorListener() {

            @Override
            public void onErrorResponse(VolleyError error) {
                Log.d("Log : ","Task Create Failure");
            }
        });

        // Adding request to request queue
        AppController.getInstance().addToRequestQueue(strReq, tag_string_req);


    }

}
