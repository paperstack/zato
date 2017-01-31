@service
Feature: zato.service.get-list
  Returns a list of services defined on a given server.

  @service.get-list
  Scenario: Upload package

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.service.upload-package"

    Given format "JSON"
    Given request "service_upload.json"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"

    When the URL is invoked

    Then status is "200"
    And I sleep for "1"

  @service.get-list
  Scenario: Get service by name

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.service.get-by-name"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/name" in request is "test-service.test-service"
    When the URL is invoked

    Then status is "200"

    And JSON Pointer "/zato_service_get_by_name_response/name" is "test-service.test-service"
    And I store "/zato_service_get_by_name_response/id" from response under "service_id"

  @service.get-list
  Scenario: Invoke service by name

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.service.invoke"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/name" in request is "test-service.test-service"
    # payload sent as base64 {"test_output": "Test Output"}
    Given JSON Pointer "/payload" in request is "eyJzZXJ2aWNlX3JlcXVlc3QiOiAiaG9sYSJ9Cg=="
    Given JSON Pointer "/data_format" in request is "json"
    When the URL is invoked

    Then status is "200"

    And JSON Pointer "/zato_env/result" is "ZATO_OK"
    And JSON Pointer "/zato_service_invoke_response/response" is base64 JSON which pointer "/response/service_response/echo_request" has "hola"

  @service.get-list
  Scenario: Get service list

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.service.get-list"
    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/name_filter" in request is "test-service.test-service"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"
    And JSON Pointer "/zato_service_get_list_response" isn't an empty list

  @service.get-list
  Scenario: Delete test service

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.service.delete"
    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/id" in request is "#service_id"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"
