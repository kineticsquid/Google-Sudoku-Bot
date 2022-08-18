def process_input_image(conversation_response, session_id, bw_input_puzzle_image):

    def process_image():
        height, width = bw_input_puzzle_image.shape
        log('!!!!!!!!!!!!! Input image dimensions: %s x %s.' % (height, width))
        if height > MAX_IMAGE_HEIGHT:
            reduction = int(np.log2(height / MAX_IMAGE_HEIGHT)) + 1
            new_dim = (int(width / 2 ** reduction), int(height / 2 ** reduction))
            resized_image = cv2.resize(bw_input_puzzle_image, new_dim)
            height, width = resized_image.shape
            log("!!!!!!!!!!!!! Reduced input image by factor of %s. New dimensions: %s x %s." % (2**reduction, height, width))


        input_matrix, image_with_ocr, image_with_lines, coordinates = \
            image_utils.extract_matrix_from_image(bw_input_puzzle_image, flask_app=flask_app)
        log('!!!!!!!!!!!!! finished image processing')
        log('Input matrix: %s' % input_matrix)
        now = datetime.now()
        ocr_image_filename = urllib.parse.quote('/ocr-input/%s.%s.png' % (get_context(session_id, INPUT_IMAGE_ID),
                                                                            now.strftime('%H-%M-%S')))
        ocr_image_bytes = cv2.imencode('.png', image_with_ocr)
        runtime_cache.setex(ocr_image_filename, REDIS_TTL, ocr_image_bytes[1].tobytes())

        lines_image_filename = urllib.parse.quote(
            '/ocr-lines/%s.%s.png' % (get_context(session_id, INPUT_IMAGE_ID),
                                        now.strftime('%H-%M-%S')))
        lines_image_bytes = cv2.imencode('.png', image_with_lines)
        runtime_cache.setex(lines_image_filename, REDIS_TTL, lines_image_bytes[1].tobytes())

        input_image_filename = urllib.parse.quote(
            '/input-image/%s.%s.png' % (get_context(session_id, INPUT_IMAGE_ID),
                                        now.strftime('%H-%M-%S')))
        input_image_bytes = cv2.imencode('.png', bw_input_puzzle_image)
        runtime_cache.setex(input_image_filename, REDIS_TTL, input_image_bytes[1].tobytes())
        set_context(session_id, PUZZLE_INPUT_IMAGE_URL, input_image_filename)
        # Need this step to convert coordinates from int64 to int so they can me converted to string
        int_coordinates = []
        for i in range(len(coordinates)):
            new_row = []
            for j in range(len(coordinates[i])):
                new_pair = []
                for k in range(len(coordinates[i][j])):
                    new_pair.append(int(coordinates[i][j][k]))
                new_row.append(new_pair)
            int_coordinates.append(new_row)

        set_context(session_id, PUZZLE_INPUT_IMAGE_COORDINATES, int_coordinates)

        # This next step is to convert from numpy array (which can't be automatically serialized)
        # to a list, which can. If the sum of the input matrix returned from image processing is 0 is meas
        # we couldn't extract the numbers from the image
        if sum(sum(input_matrix)) > 0:
            matrix_as_list = []
            for row in input_matrix:
                new_row = []
                for number in row:
                    new_row.append(int(number))
                matrix_as_list.append(new_row)
            set_context(session_id, PUZZLE_INPUT_MATRIX, matrix_as_list)


    # If SMS then fork and spew messages
    process_image()

    return conversation_response